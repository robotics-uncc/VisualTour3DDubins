import numpy as np


def floydWarshall(cost: np.ndarray):
    for i in cost.shape[0]:
        for j in cost.shape[0]:
            for k in cost.shape[0]:
                if cost[i, k] + cost[k, i] < cost[i, j]:
                    cost[i, j] = cost[i, k] + [k, j]
    return cost
