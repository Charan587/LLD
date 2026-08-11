"""so here we have class as ride , different types of algorithm , vehicle , booking class

so assumptions are we have only alogirthm and ride class and combined booking class tracking ride and aklgorthm , assuming we multiply flat when airport with surge

used algo - inheritence , stratergy 

"""
from dataclasses import dataclass, field

@dataclass(frozen=True)
class Ride:
    km : int
    minutes : int
    typeOfVehicle : str


class Algorithm:
    def calculate(self,ride : Ride ):...

class PerKmAlgo(Algorithm):
    def __init__(self, per_km):
        self.per_km = per_km

    def calculate(self,ride):
        return ride.km * self.per_km

class PerMinuteAlgo(Algorithm):
    def __init__(self, per_minute):
            self.per_minute = per_minute
    
    def calculate(self,ride):
        return ride.minutes * self.per_minute

class HybridAlgo(Algorithm):
    def __init__(self,base_cost,per_km,per_minute):
        self.base_cost = base_cost
        self.per_km = per_km
        self.per_minute = per_minute

    def calculate(self, ride):
        return self.base_cost + (ride.km * self.per_km) + (ride.minutes * self.per_minute)

class FlatAlgo(Algorithm):
    def __init__(self, base_cost):
        self.base_cost = base_cost

    def calculate(self, ride):
        return self.base_cost

class Booking:

    def __init__(self,algorithms:dict[Algorithm], surge , min_base_cost):
        self.algorithms = algorithms
        self.surge = surge
        self.min_base_cost = min_base_cost

    def calculate(self, ride : Ride , algorithm : Algorithm= None , type_of_run= None):
        if algorithm:
            algo = algorithm

        elif type_of_run == "AIRPORT":
            algo = self.algorithms["AIRPORT"]

        else:
            algo = self.algorithms[ride.typeOfVehicle]

        return max(
            algo.calculate(ride) * self.surge,
            self.min_base_cost
        )
        






if __name__ == "__main__":


    per_km_cost = PerKmAlgo(12)
    per_minute = PerMinuteAlgo(2)
    hybrid = HybridAlgo(50 ,10 , 1)
    flat = FlatAlgo(500)


    ride1 = Ride(10,25,"AUTO")
    assert per_km_cost.calculate(ride1) == 120
    assert per_minute.calculate(ride1) == 50
    assert hybrid.calculate(ride1) == 175
    assert flat.calculate(ride1) == 500

    booking = Booking({"MINI":per_km_cost,"AUTO":per_minute,"SEDAN":hybrid,"AIRPORT":flat,"SUV":hybrid}, surge=1 , min_base_cost = 60)

    assert booking.calculate(ride1) == 60

    ride2 = Ride(5,30,"AUTO")

    assert booking.calculate(ride2) == 60

    booking.surge=1.5

    assert booking.calculate(ride1, hybrid) == 262.5
    assert booking.calculate(ride1, per_minute) == 75

    print("all test passed")



