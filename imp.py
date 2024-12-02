import random


#decoraters
class User_Class:
    def __init__(self,name):
        self.name = name
        self.logging = False

def Athonication_decoreter(function):
    def wrapper(*args,**kwargs):
        if args[0].logging==True:
            # args[0] ----block_post(new_user) take user_name from indast 0 i.e ==new_user
            function(args[0])
    return wrapper

@Athonication_decoreter
def block_post (user):
    print(f"This is {user.name} blog")



new_user = User_Class("vaishnavi")
logging = True
block_post(new_user)



# add variales in htmla

@app.routh('/')
def home():
    randon_number = random.randint(2,9)
    return render_template("index.html", num = randon_number)