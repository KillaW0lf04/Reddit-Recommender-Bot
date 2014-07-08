#! /usr/bin/python
# ~*~ coding: utf-8 ~*~
from __future__ import division, print_function

import os
import numpy as np

import textparser

from datasource import load_data_source
from hashedindex import HashedIndex, load_meta
from utils import search_files

if __name__ == '__main__':

    import time
    t0 = time.time()

    # Lancaster Stemmer is very very slow
    _stemmer = textparser.NullStemmer()

    data_path = '/home/michaela/Development/Reddit-Testing-Data'
    save_path = '/home/michaela/Development/python_sr.json.bz2'

    # Set the parameters to the program over here
    force_reindex = False
    parameters = {
        'samples': 800,
        'subreddit': 'python',
        'min_frequency': 0.06,
        'max_frequency': 1.00,
        'stemmer': str(_stemmer),
        'mode': 'tfidf',
    }

    print(parameters)
    print('Available pages: ', len(list(search_files(os.path.join(data_path, 'pages')))))

    sr_index = HashedIndex()

    if os.path.exists(save_path):
        # Possible to initially just load meta-data?
        meta = load_meta(save_path, compressed=True)
    else:
        meta = None
        force_reindex = True

    if force_reindex or meta['parameters'] != parameters:
        print('State File Parameters out of date. Re-Indexing...')

        t0 = time.time()
        sr_index.clear()
        data = load_data_source(
            sr_index, data_path,
            subreddit=parameters['subreddit'],
            page_samples=parameters['samples'],
            preprocess=textparser.clean_token
        )

        print('Original shape: (%d, %d)' % (len(sr_index.documents()), len(sr_index.terms())))

        # Values larger than 0.01 for min_frequency can be considered "aggressive" pruning
        t3 = time.time()

        sr_index.prune(min_frequency=parameters['min_frequency'], max_frequency=parameters['max_frequency'])
        sr_index.save(save_path, compressed=True, text_class=data, parameters=parameters)

        print('Pruning Runtime: {}'.format(time.time() - t3))
        print('Indexing Runtime: {}'.format(time.time() - t0))
    else:
        print('State File is up to date')
        meta = sr_index.load(save_path, compressed=True)
        data = meta['text_class']

    print()
    print('Generating feature matrix')

    t1 = time.time()
    X = sr_index.generate_feature_matrix(mode=parameters['mode'])
    sr_index.freeze()  # Prevent more terms from being added

    print('generation runtime = {}'.format(time.time() - t1))

    print('Feature Matrix shape: (%d, %d)' % X.shape)

    # TODO: Move the generator code below to a function
    # This needs to be better tested, not sure if this is 100% correct
    y = np.zeros(len(sr_index.documents()))
    for index, doc in enumerate(sr_index.documents()):
        y[index] = 0 if data[doc] is None else 1

    print(y)

    print()
    print('Unlabelled: ', np.sum(y == 0))
    print('Positive: ', np.sum(y == 1))

    from sklearn.cross_validation import StratifiedKFold
    from sklearn.metrics import *

    n = 4  # Number of folds

    kf = StratifiedKFold(y, n_folds=n)
    accuracy = np.zeros(n)
    precision = np.zeros(n)
    recall = np.zeros(n)
    f1 = np.zeros(n)
    cm = np.zeros((2, 2))

    # SVM
    # Note: Optimised values of C are data-dependent and cannot be set
    # with some pre-determined value. They need to be optimised with a
    # cross validation study in order to make the most use of them.

    classifier = None
    for index, (train, test) in enumerate(kf):
        from sklearn.svm import SVC
        classifier = SVC(kernel='linear', C=1.0)

        classifier.fit(X[train], y[train])
        y_pred = classifier.predict(X[test])

        # Store the measures obtained
        accuracy[index] = accuracy_score(y[test], y_pred)
        precision[index] = precision_score(y[test], y_pred)
        recall[index] = recall_score(y[test], y_pred)
        f1[index] = f1_score(y[test], y_pred)

        cm += confusion_matrix(y[test], y_pred)

    # Average scores across the K folds
    print()
    print('Performance Metrics')
    print('-------------------')
    print('(Using %s)' % str(classifier))
    print('Accuracy: ', accuracy.mean())
    print('Precision: ', precision.mean())
    print('Recall: ', recall.mean())
    print('F1: ', recall.mean())

    print()
    print('Confusion Matrix')
    print('----------------')
    print('(Unlabelled vs Positive)')
    print(cm)
