import os
import sys
import numpy as np
import pickle
import io
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import scale
from sklearn.metrics import f1_score
from sklearn.multiclass import OneVsRestClassifier
from sklearn.multioutput import MultiOutputClassifier
from sklearn.linear_model import SGDClassifier

from utils import common_tools as ct
from utils.data_handler import DataHandler as dh
# from utils.draw_graph import DrawGraph as dg
from utils.lib_ml import MachineLearningLib as mll
from utils.env import *

def classification(X, params):
    res = {}
    X_scaled = scale(X)
    ground_truth_path=os.path.join(DATA_PATH, params["data"],params["ground_truth"])
    y = dh.load_ground_truth(ground_truth_path)
    y = y[:len(X)]
    #print(X_scaled.shape)
    #print(len(y))
    #print("y_0=",y[0])
    acc = 0.0
    micro_f1 = 0.0
    macro_f1 = 0.0
    n_train = params["n_train"]
    print("number_of_train_set", n_train)
    for _ in range(params["times"]):
        X_train, X_test, y_train, y_test = X[:n_train, :], X[n_train:, :], y[:n_train], y[n_train:]
        clf = getattr(mll, params["model"]["func"])(X_train, y_train, params["model"])
        ret = mll.infer(clf, X_test, y_test)
        acc += ret[1]
        y_score = ret[0]
        micro_f1 += f1_score(y_test, y_score, average='micro')
        macro_f1 += f1_score(y_test, y_score, average='macro')

    acc /= float(params["times"])
    micro_f1 /= float(params["times"])
    macro_f1 /= float(params["times"])
    res = {"acc" : acc, "micro_f1": micro_f1, "macro_f1": macro_f1}
    print({"acc" : acc, "micro_f1": micro_f1, "macro_f1": macro_f1})
    return res


def params_handler(params, info, pre_res):
    if "res_home" not in params:
        params["res_home"] = info["res_home"]
    if "embeddings_file" in params:
        params["embeddings_path"] = os.path.join(info["home_path"], params["embeddings_file"])
    elif "infer" in pre_res and "entity_embedding_path" in pre_res["infer"]:
        params["embeddings_path"] = pre_res["infer"]["entity_embedding_path"]
    elif "optimize" in pre_res and "entity_embedding_path" in pre_res["optimize"]:
        params["embeddings_path"] = pre_res["optimize"]["entity_embedding_path"]
    return {}


@ct.module_decorator
def metric(params, info, pre_res, **kwargs):
    res = params_handler(params, info, pre_res)

    # load embeddings 
    if params["file_type"] == "txt":
        embedding_path=os.path.join(DATA_PATH, "experiment", params["embeddings_file"])
        node_path=os.path.join(DATA_PATH, params["data"], "node.txt")
        node_file=open(node_path, 'r')
        nodes=node_file.readlines()
        node_num=len(nodes)
        node_file.close()
        X = dh.load_embedding(embedding_path, params["file_type"], node_num)
    else:
        X = dh.load_embedding(params["embeddings_path"], params["file_type"])

    # results include: accuracy, micro f1, macro f1
    metric_res = classification(X, params)

    # insert into res
    for k, v in metric_res.items():
        res[k] = v

    return res
