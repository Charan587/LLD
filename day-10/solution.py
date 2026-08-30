"""
This is also a single class but it will be public . and need to create an object to acquire we have to take care of that abd every service we ill send pool while creating

assumptions -  one class and getting a object and using that object to create instance. single threaded. 

"""
# get_instance() twice → the same object (is, not ==)
# fresh pool, max_size=3 → available == 3, in_use == 0
# after one acquire → available == 2, in_use == 1
# after three acquires → available == 0, in_use == 3
# the fourth acquire → error (the boundary: the third must succeed)
# release one → available == 1, in_use == 2
# releasing the same connection twice → error
# releasing a connection the pool never issued → error
# max_size=0 and max_size=-1 → error
# acquire, release, acquire again → you get a working connection, and counts are right
# get_instance(max_size=10) after get_instance(max_size=3) — assert whatever you decided in requirement 8, and comment why
# OrderService under a pool that always fails to acquire — assert the service surfaces that, without editing OrderService
# two independent pools coexisting, one with max_size=2 and one with max_size=5, neither affecting the other

from collections import defaultdict
from dataclasses import dataclass


@dataclass
class Connection:
    name:str='DB'

class ConnectionPool:

    _instance=None

    def __init__(self,max_size:int=3):
        if max_size<=0:
            raise ValueError(f"max_size should be positive, got {max_size}")
        self.max_size = max_size
        self._free =[f"conn{i}" for i in range(max_size)]
        self._in_use = set()
      
    @classmethod
    def get_instance(cls,max_size:int = 3):
        if cls._instance is None:
            cls._instance = cls(max_size)
        return cls._instance

    @property
    def available(self):
        return len(self._free)

    @property
    def in_use(self):
        return len(self._in_use)

    def acquire(self):
        if not self._free:
            raise RuntimeError("pool exhausted")

        conn = self._free.pop()
        self._in_use.add(conn)
        return conn

    def release(self,conn):
        if conn not in self._in_use:
            raise ValueError(f"{conn} not in use")
        self._in_use.remove(conn)
        self._free.append(conn)


class AlwaysFailConnectionPool:

    def acquire(self):
        raise ValueError("nothing to acquire")

    def release(self):
        pass

class OrderService:

    def __init__(self,pool):
        self.pool=pool



def raises(fn,*args):
    try:
        fn(*args)
    except:
        return True
    return False

if __name__ =="__main__":


    conn1 = ConnectionPool.get_instance(max_size=3)
    conn2 = ConnectionPool.get_instance(max_size=3)

    assert conn1 is conn2
    assert conn1.available ==3
    assert conn1.in_use== 0
    con = conn1.acquire()
    assert conn1.available==2
    assert conn1.in_use == 1
    con2 = conn1.acquire()
    con3 = conn1.acquire()
    assert conn1.available==0
    assert conn1.in_use == 3

    assert raises(conn1.acquire)==True

    conn1.release(con)
    assert conn1.available==1
    assert conn1.in_use == 2

    assert raises(conn1.release,con)==True

    con4 = Connection()

    assert raises(conn1.release,con4) == True

    # only one connection is done even if we are going to create max size of 10

    small,big = ConnectionPool(max_size=3),ConnectionPool(max_size=10)
    assert small is not big

    conn1 = ConnectionPool.get_instance(max_size=3)
    conn2 = ConnectionPool.get_instance(max_size=10)

    assert conn1 is conn2

    failPool = AlwaysFailConnectionPool()

    order = OrderService(pool= failPool)

    assert raises(order.pool.acquire)

    print("all test case passed")







