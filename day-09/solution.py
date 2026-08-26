"""
a big fat class containing all methods . 

classes are -> single big Sql() class.
methods are -> all select , from etc

assumptions -> single threasded ( i will tell and keep this default even if i am not sure nt just to add)
always assumping select as string and limit and offset as integers

rejected design - we can add multiple where in a single where by using *args
we can have multiple order by by using *args and considering last one as direction if it has "DESC" or "ASC" only on these terms its considered.
for joins we can have additional param called type of join and we can have muktiple join as Inner , Outer and many oither thing track type of joins and join everyone at build

patterns used is builder pattern , single responsibilty 
"""
def validator(s:int):
    if s<0:
        raise ValueError("only greater than zero is accepted")
class Sql:

    def __init__(self):
        self.cols="*"
        self._table=None
        self._joins: dict[str, str] = {}
        self._wheres=[]
        self._order_by:dict[str, str] = {}
        self._limit = None
        self._offset = None

    def select(self,*args:str):
        l = []
        for arg in args:
            l.append(arg)

        self.cols = ", ".join(l)
        return self

    def from_(self,table:str):
        self._table=table
        return self

    def where(self,*args):
        for arg in args:
            self._wheres.append(arg)
        return self

    def join(self,table:str,condition:str):
        self._joins[table]=condition
        return self

    def limit(self,s:int):
        validator(s)

        self._limit=s
        return self

    def offset(self,s:int):
        validator(s)

        self._offset=s
        return self

    def order_by(self,c:str,direction:str="ASC"):
        self._order_by['col']=c
        self._order_by['d']=direction
        return self

    def build(self):
        if self._table is None:
            raise ValueError("no table")

        parts = [f"SELECT {self.cols} FROM {self._table}"]

        for table, on in self._joins.items():
            parts.append(f"INNER JOIN {table} ON {on}")
        if self._wheres:
            parts.append("WHERE " + " AND ".join(self._wheres))
        if self._order_by:
            parts.append(f"ORDER BY {self._order_by['col']} {self._order_by['d']}")
        if self._limit is not None:
            parts.append(f"LIMIT {self._limit}")
        if self._limit is None and self._offset is not None:
            raise ValueError("only offset is there no limit")
        if self._offset is not None:              # is not None, NOT `if self._offset`
            parts.append(f"OFFSET {self._offset}")

        return " ".join(parts)



    
    

    
    




if __name__ =="__main__":

    assert Sql().select("id","name").from_("users").build() == "SELECT id, name FROM users"
    assert Sql().from_("users").build() == "SELECT * FROM users"
    assert Sql().from_("users").where("age > 18").build() == "SELECT * FROM users WHERE age > 18"
    assert Sql().from_("users").where("age > 18").where("active = 1").build() == "SELECT * FROM users WHERE age > 18 AND active = 1"
    assert Sql().select("u.name").from_("users u").join("orders o", "u.id = o.user_id").build() ==  "SELECT u.name FROM users u INNER JOIN orders o ON u.id = o.user_id"
    assert Sql().select("u.name").from_("users u").join("orders o", "u.id = o.user_id").join("payment p", "u.id = p.user_id").build() ==  "SELECT u.name FROM users u INNER JOIN orders o ON u.id = o.user_id INNER JOIN payment p ON u.id = p.user_id"
    assert Sql().from_("users").order_by("created_at","DESC").limit(10).build() == "SELECT * FROM users ORDER BY created_at DESC LIMIT 10"
    assert Sql().from_("users").order_by("name").build() == "SELECT * FROM users ORDER BY name ASC"
    assert Sql().from_("users").limit(10).offset(20).build() == "SELECT * FROM users LIMIT 10 OFFSET 20"
    assert Sql().from_("users").limit(10).offset(0).build() == "SELECT * FROM users LIMIT 10 OFFSET 0"
    assert Sql().select("u.name").from_("users u").join("orders o", "u.id = o.user_id").build() ==  "SELECT u.name FROM users u INNER JOIN orders o ON u.id = o.user_id"
    assert Sql().from_("users u").join("orders o", "u.id = o.user_id").join("payment p", "u.id = p.user_id").select("u.name").build() ==  "SELECT u.name FROM users u INNER JOIN orders o ON u.id = o.user_id INNER JOIN payment p ON u.id = p.user_id"
    assert Sql().from_("users").limit(10).order_by("created_at","DESC").build() == "SELECT * FROM users ORDER BY created_at DESC LIMIT 10"
    # assert Sql().select("id","name").build()
    print("all checks passed")

    