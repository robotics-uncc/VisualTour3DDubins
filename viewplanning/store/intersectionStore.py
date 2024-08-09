import pyvista as pv
import numpy as np
import os
import logging
import pymeshfix as mf
from viewplanning.configuration import ConfigurationFactory
import subprocess
import multiprocessing



CACHE_SIZE = 50
APPROX_ZERO = 1e-2


class IntersectionStore:
    '''
    intersect meshes with pyvista and store the results
    '''
    __instance: 'dict[int, IntersectionStore]' = {}

    def __init__(self):
        self.lookup: dict[(str, str), pv.PolyData] = {}
        self.queue = []

    def intersect(self, a: pv.PolyData, b: pv.PolyData, aId: str, bId: str):
        '''
        intersect mesh a and b with corresponding ids aId and bId and store them in the cache using the ids

        Parameters
        ----------
        a: pv.PolyData
            mesh to intersect
        b: pv.PolyData
            mesh to intersect
        aId: str
            id of mesh a
        bId: str
            id of mesh b
        
        Returns
        -------
        mehs intersection of a and b
        '''
        if (aId, bId) in self.lookup:
            return self.lookup[(aId, bId)]
        if (bId, aId) in self.lookup:
            return self.lookup[(aId, bId)]
        _, _, _, _, az0, _ = a.bounds
        _, _, _, _, bz0, _ = b.bounds
        if abs(bz0 - az0) < APPROX_ZERO:
            b: pv.PolyData = b.transform(np.array([
                [1, 0, 0, 0],
                [0, 1, 0, 0],
                [0, 0, 1, APPROX_ZERO],
                [0, 0, 0, 1]
            ]))
        _, numCollisions = a.collision(b, contact_mode=1)
        if numCollisions <= 0:
            return None
        
        if len(self.queue) >= CACHE_SIZE:
            logging.debug('popping intersection cache')
            key = self.queue.pop()
            self.lookup.pop(key)

        intersection = pyVistaIntersection(a, b)

        self.lookup[(aId, bId)] = intersection
        self.queue.append((aId, bId))
        return intersection

    def clearCache(self):
        '''
        clear in memory cache of intersections
        '''
        self.queue.clear()
        self.lookup.clear()

    @ staticmethod
    def getInstance():
        '''get an intersection store for the current process id'''
        pid = os.getpid()
        config = ConfigurationFactory.getInstance()
        
        if pid not in IntersectionStore.__instance:
            if config['intersection']['type'] == 'drive':
                IntersectionStore.__instance[pid] = DriveIntersectionStore(config['intersection']['folder'])
            elif config['intersection']['type'] == 'memory':
                IntersectionStore.__instance[pid] = IntersectionStore()
        return IntersectionStore.__instance[pid]


class DriveIntersectionStore(IntersectionStore):
    '''get intersections stored in a folder'''
    def __init__(self, folder=None, write=False, blender=False):
        '''
        Parameters
        ----------
        folder: str
            path to directory storing mesh intersections
        write: bool
            calculate mesh intersections and write then to the folder
        blender: bool
            use blender isntead of pyvista to calculate intersections
        '''
        self.folder = folder
        self.write = write
        self.blender = blender

    def intersect(self, a: pv.PolyData, b: pv.PolyData, aId: str, bId: str):
        if os.path.exists(self.folder + self.transformIds(aId, bId)):
            file = self.folder + self.transformIds(aId, bId)
        elif os.path.exists(self.folder + self.transformIds(bId, aId)):
            file = self.folder + self.transformIds(bId, aId)
        else:
            if self.write and not self.blender:
                return self.store(a, b, aId, bId)
            elif self.write and self.blender:
                return blenderIntersection(self.idToPath(aId), self.idToPath(bId), self.folder + self.transformIds(aId, bId))
            else:
                return None
            
        reader = pv.get_reader(file)
        intersection: pv.PolyData = reader.read()
        return intersection

    
    def store(self, a: pv.PolyData, b: pv.PolyData, aId: str, bId: str):
        ax0, ax1, ay0, ay1, az0, az1 = a.bounds
        bx0, bx1, by0, by1, bz0, bz1 = b.bounds


        if abs(bz0 - az0) < APPROX_ZERO:
            b: pv.PolyData = b.transform(np.array([
                [1, 0, 0, 0],
                [0, 1, 0, 0],
                [0, 0, 1, APPROX_ZERO],
                [0, 0, 0, 1]
            ]))
        # bounding box intersection
        if bx0 > ax1 or bx1 < ax0 or by0 > ay1 or by1 < ay0 or bz0 > az1 or bz1 < az0:
            return None
        _, numCollisions = a.collision(b, contact_mode=1)
        if numCollisions <= 0:
            return None
        file = self.folder + self.transformIds(aId, bId)
        intersection = pyVistaIntersection(a, b) if not self.blender else blenderIntersection(aId, bId, file)
        intersection.save(file)
        return intersection
    
    def transformIds(self, aId, bId):
        return aId.replace('.ply', '') + '--' + bId.replace('.ply', '') + '.ply'
    
    def idToPath(self, id):
        split = id.split('--')
        if len(split) > 1:
            return self.folder + id
        return self.folder + '../' + id

    def clearCache(self):
        pass


def blenderIntersection(a, b, out):
    '''
    intersect two meshes using blender

    Parameters
    ----------
    a: str
        path to mesh a
    b: str
        path to mesh b
    out: str
        destination for new mesh
    
    Returns
    -------
    pv.PolyData | None
        mesh intersection
    '''
    subprocess.run([
        'blender', '-b', '--python', 'viewplanning/store/blenderIntersect.py',
        '--',
        '--a', a,
        '--b', b,
        '--out',out
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    if not os.path.exists(out):
        return None
    reader = pv.get_reader(out)
    return reader.read()

def pyVistaIntersection(a, b):
    '''
    use pyvista to intersect meshes

    Parameters
    ----------
    a: pv.PolyData
        mesh a
    b: pv.PolyData
        mesh b
    
    Returns
    -------
    pv.PolyData | None
        mesh intersection
    '''
    # use seperate process because sometimes intersecion crashes without exception
    q = multiprocessing.Queue()
    p = multiprocessing.Process(target=_boolean_intersection, args=[a, b, q])
    p.start()
    p.join(timeout=10)
    if p.exitcode is None:
        p.terminate()
        logging.warn('intersection failed')
        return None
    intersection = q.get()
    q.close()
    return intersection

def _boolean_intersection(a: pv.PolyData, b: pv.PolyData, queue: multiprocessing.Queue):
    intersection = a.boolean_intersection(b)
    if intersection.number_of_cells <= 0:
        b: pv.PolyData = b.transform(np.array([
            [1, 0, 0, 0],
            [0, 1, 0, 0],
            [0, 0, 1, APPROX_ZERO * 10],
            [0, 0, 0, 1]
        ]))
        intersection = b.boolean_intersection(a)
    intersection = intersection.triangulate()
    if not intersection.is_all_triangles:
        logging.warn('failed to triangulate two meshes')
        return None
    meshfix = mf.MeshFix(intersection)
    meshfix.repair()
    queue.put(meshfix.mesh)