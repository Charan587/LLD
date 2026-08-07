class Hotel:
    def __init__(self,price):
        self.price=price
        self.rooms=[]
        self.availability={}

    def add_rooms(self, room):
        self.rooms.append(room)

    def check_availability(self,room, from_date, to_date):
        if room not in self.rooms:
            return False , "Room not found"
        if room not in self.availability:
            return True, "Room is available"
        for booked_from, booked_to in self.availability[room]:
            if from_date >=booked_from and to_date <= booked_to:
                return False, "Room is not available"
            elif from_date <=booked_from and to_date >=booked_to:
                return False, "Room is not available"
            elif from_date <=booked_from and to_date >=booked_from:
                return False, "Room is not available"
        return True, "Room is available"

    def book_room(self, room, from_date, to_date):
        available, message = self.check_availability(room, from_date, to_date)
        if not available:
            return False, message
        if room not in self.availability:
            self.availability[room]=[]
            self.availability[room].append((from_date, to_date))
        else:
            self.availability[room].append((from_date, to_date))
        return True, "Room booked successfully"

    def cancel_booking(self, room, from_date, to_date):
        if room not in self.availability:
            return False , "No booking found for this room"
        for booked_from, booked_to in self.availability[room]:
            if booked_from == from_date and booked_to ==to_date:
                self.availability[room].remove((booked_from, booked_to))
                return True, "Booking cancelled successfully"
        return False, "No booking found for this room"

    def find_available_rooms(self, from_date, to_date):
        available_rooms=[]
        for room in self.rooms:
            available, message = self.check_availability(room, from_date, to_date)
            if available:
                available_rooms.append(room)
        return available_rooms

    def price_of_room(self, from_date=None,to_date=None , nights=0):
        price = self.price *nights if nights>1 else self.price * (to_date - from_date).days
        return price, "Price of the room is {}".format(price)



        


if __name__ == "__main__":
    hotel= Hotel(100)
    hotel.add_rooms(1)
    hotel.add_rooms(2)
    hotel.add_rooms(3)

    