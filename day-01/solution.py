from datetime import date


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
    for r in (101,102,103): hotel.add_rooms(r)
    from datetime import date
    d = lambda x: date(2026,8,x)  
    hotel.add_rooms(1)
    hotel.add_rooms(2)
    hotel.add_rooms(3)

    print('1. normal booking 1->5 :', hotel.book_room(1, d(1), d(5)))
    print('2. exact overlap 1->5  :', hotel.book_room(1, d(1), d(5)))
    print('3. inside 2->4         :', hotel.book_room(1, d(2), d(4)))
    print('4. RIGHT overlap 3->8  :', hotel.book_room(1, d(3), d(8)), ' <-- should be REJECTED')
    print('5. back-to-back 5->7   :', hotel.book_room(1, d(5), d(7)), ' <-- should be ACCEPTED')
    print()
    print('bookings on 1:', hotel.availability.get(1, []))
    print()
    print('6. find_available 1->5 :', hotel.find_available_rooms(d(1), d(5)))
    print('7. bad range 5->1      :', hotel.book_room(2, d(5), d(1)), ' <-- should be REJECTED')
    print('8. missing room 999    :', hotel.book_room(3, d(1), d(5)))
    try:
        print('9. price nights=1      :', hotel.price_of_room(nights=1))
    except Exception as e:
        print('9. price nights=1      : CRASH ->', type(e).__name__, e)
    print('10. price 1->5         :', hotel.price_of_room(d(1), d(5)))


    