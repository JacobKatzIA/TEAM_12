import psycopg2
from psycopg2 import Error
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import re

app = Flask(__name__)
app.secret_key = 'din_hemliga_nyckel'
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'index'

def get_user(username): #Funktionen hämtar användarnamnet från en specifik användare
  try:
      connection = psycopg2.connect( #Databasanslutningsuppgifter
        user="ap2204",
        password="if7fupb5",
        host="pgserver.mau.se",
        port="5432",
        database="ap2204"
      )
      cursor = connection.cursor() #Anslutningen till databasen öppnas och är beredd att importa/exportera uppgifter
      cursor.execute('SELECT m_id, password FROM members WHERE username = %s', (username,)) #Anropar till databasen att hämta ut användarnamnet där användarens ID och lösenord stämmer överrens med varandra i tabellen members
      user_data = cursor.fetchone() #user_data blir namnet på det hämtade användarenamnet
      cursor.close() #Anropet för att hämta specifik data från en rad/tabell i databasen stängs
      connection.close() #Anslutningen till databasen stängs
      return user_data #Funktionen returnerar user_data/användarnnamn 
  except (Exception, psycopg2.Error) as error: #Om try-anropet inte fungerar, visas ett "error-meddelande upp"
    print("Fel vid hämtning av data från PostgreSQL", error) #Felmeddelandet och vilken typ av fel det är "Exempel: Error 404"
    
class User(UserMixin): #Klassen är en mixin-klass  från "Flask-Login" som ger användbara metoder för användarhantering
  def __init__(self, m_id, username): #Definierar initialiseringsmetoden (__init__) som körs när ett nytt User-objekt skapas
    self.id = m_id #Sätter instansens id-attribut till det givna användarID:et "m_id"
    self.username = username #Sätter instansens username-attribut till det givna användarnamnet
    
  def get_id(self): #Funktionen get_id returnerar användarens id som en sträng
     return str(self.id)
    
@login_manager.user_loader #Funktionen specificerar hur användare ska laddas från databasen när de loggar in
def load_user(user_id):
  connection = None
  cursor = None
  try:
    connection = psycopg2.connect(
      user="ap2204",
      password="if7fupb5",
      host="pgserver.mau.se",
      port="5432",
      database="ap2204"
    )
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM members WHERE m_id = %s", (user_id,)) #Utför en SQL-fråga för att hämta användardata baserat på användarID "m_id"
    user_data = cursor.fetchone() #Hämtar resultatet från SQL-frågan
    if user_data is None: #Om ingen användare hittades, returnera None
      return None
    username = user_data[2] #Hämtar ut användarnamnet från den tredje kolumnen i tabellen från databasen
    return User(user_id, username)
  except (Exception, psycopg2.Error) as error:
    print("Fel vid hämtning från PostgreSQL", error)
    return None
  finally:
    if cursor:
      cursor.close()
    if connection:
        connection.close()
        
@app.route('/logout') #Användaren loggas ut från sidan och skickas till inloggningssdian "index.html"
def logout():
  logout_user()
  return redirect(url_for('index'))

@app.route('/delete_account', methods=['POST']) #Funktionen raderar ett befintligt konto
@login_required
def delete_account():
  m_id = current_user.get_id() #Hämtar ut m_id från den befintliga inloggade användaren som utför anropet
  try:
    connection = psycopg2.connect(
      user="ap2204",
      password="if7fupb5",
      host="pgserver.mau.se",
      port="5432",
      database="ap2204"
    )
    cursor = connection.cursor() 
    #m_id är en ForeignKey till följande tabeller nedan. Därav raderas information kopllad till den i följande funktioner.
    cursor.execute("DELETE FROM meallog WHERE m_id = %s", (m_id,)) #Tar bort sparad data i måltidslogg
    
    cursor.execute("DELETE FROM workoutdetails WHERE workoutid IN (SELECT workoutid FROM workouts WHERE m_id = %s)", (m_id,)) #Tar bort sparad data från träningslogg
    
    cursor.execute("DELETE FROM workouts WHERE m_id = %s", (m_id,)) #Tar bort data kopplad till träningslogg och m_id
    
    cursor.execute("DELETE FROM members WHERE m_id = %s", (m_id,)) #Tar bort den primära nycklen m_id
    
    connection.commit()
    logout_user() #Användaren slussas till inloggningssidan och kan inte längre logga in med det raderade kontot
    flash('Ditt konto har raderats.', 'success') #Ett återkopplingsmeddelande visas för användaren där lyckad konto radering har gjorts
    return redirect(url_for('index'))
  except (Exception, psycopg2.Error) as error: #Om det inte går att radera kontot visas följande error-meddelande
    print("Fel uppstod vid försök av att radera ett konto: ", error)
    flash('Kunde inte radera konto.', 'error')
    return redirect(url_for('start'))
  finally:
    if cursor:
      cursor.close()
    if connection:
      connection.close()
        
    return redirect(url_for('index'))

@app.route('/change_credentials', methods=['GET', 'POST']) #Funktion för att användare ska kunna änra sitt lösenord
@login_required
def change_credentials():
    if request.method == 'POST':
       current_username = request.form['current_username'] #Hämtar data från HTML-dokumentet "change_credentials.html" där användaren matat in nya uppgifter genom POST-metoden
       current_password = request.form['current_password'] 
       new_password = request.form['new_password']

       if not current_username or not current_password or not new_password: #Kollar ifall alla fällt är ifyllda annars visas ett meddelande upp
          flash("Vänligen fyll i alla fält")
          return redirect(url_for('change_credentials'))
       
       if update_credentials(current_username, current_password, new_password): #Om alla fällt är ifyllda och godkännda uppdateras lösenordet i funktionen update_credentials
          flash("Lösenordet har ändrats", "success")
          return redirect(url_for('change_credentials'))
       else:
          flash("Fel vid ändring av lösenord", "error") #Om det inte går att uppdatera lösenordet visas ett meddelande för detta
          return redirect(url_for('change_credentials'))
       
    return render_template('change_credentials.html')


def update_credentials(current_username, current_password, new_pasword): #Funktionen som ändrar lösenord i SQL-frågor
    if not re.match('^(?=.*[A-Z])(?=.*\d.*\d).{6,}$', new_pasword): #Krav på ett säkert lösenord - minst 6 tecken - minst en stor bokstav - minst två siffror
      flash("Lösenordet måste inehålla minst en stor bokstav och två siffror")
      return False
    try:
      connection = psycopg2.connect(
        user="ap2204",
        password="if7fupb5",
        host="pgserver.mau.se",
        port="5432",
        database="ap2204")
      
      cursor = connection.cursor()

      cursor.execute("SELECT * FROM members WHERE username = %s AND password = %s", (current_username, current_password)) #Utför SQL-fråga där all användarinformation hämtas
      user_exists = cursor.fetchone()

      if user_exists:
         cursor.execute("UPDATE members SET password = %s WHERE username = %s", (new_pasword, current_username)) #Uppdaterar befintligt lösenord till det nya som användaren har registrerat
         connection.commit()
         return True
      else:
         return False
      
    except (Exception, Error) as error:
        print("Fel vid uppdatering av användaruppgifter:", error)
        return False
    finally:
        if connection:
           cursor.close()
           connection.close()



def register_member(fullname, username, password, email): #Funktion för att registrera ny användare
    if not re.match('^(?=.*[A-Z])(?=.*\d.*\d).{6,}$', password):  #Krav på ett säkert lösenord - minst 6 tecken - minst en stor bokstav - minst två siffror
       flash("Lösenordet måste inehålla minst en stor bokstav och två siffror")
       return False
    try:
        connection = psycopg2.connect(
          user="ap2204",
          password="if7fupb5",
          host="pgserver.mau.se",
          port="5432",
          database="ap2204")
      
        cursor = connection.cursor()

        cursor.execute("SELECT * FROM members WHERE email = %s", (email,)) #Hämtar ut samtlig data från tabellen members där den givna emailen stämmer överrens
        if cursor.fetchone() is not None: 
            print("Användaren finns redan registrerad") #Om emailen redan finns eller annan data, registreras ej användaren och ett flash-meddelande
            return False
      
        cursor.execute("SELECT MAX(m_id) FROM members") #Hämtar det ID:et som är högst och det nya ID:et från den nya användaren får det plus ett. Det vill säga om ett befintligt ID har 34, får det nya 34+1 = 35
        latest_id = cursor.fetchone()[0]

        if latest_id is None:
          latest_id = 0

        next_id = latest_id + 1

        cursor.execute("INSERT INTO members (m_id, fullname, username, password, email) VALUES (%s, %s, %s, %s, %s)", 
                      (next_id, fullname, username, password, email)) #Den nya användarens data registreras i en ny kolumn i databasen
      
        connection.commit()
        flash("Användare registrerad") #Användaren registreras
        return True

    except (Exception, Error) as error:
        flash("Fel vid registrering:", error)
        return False
    finally:
        if connection:
           cursor.close()
           connection.close()
    

@app.route('/register_user') #Funktionen hämtar data som användaren har matat in i ett HTML-dokument. Datan matas sedan in i databasen genom funktionen register_member
def register_user():
  return render_template('register_user.html')

@app.route('/submit', methods=['POST'])
def submit():
    fullname = request.form['fullname']
    username = request.form['username']
    password = request.form['password']
    email = request.form['email']
    if not register_member(fullname, username, password, email):
       return redirect('register_user')
    else:
       return redirect('/')



@app.route('/meal', methods=['GET', 'POST']) #Användarens måltidsloggar registreras i följande funktion
@login_required
def log_meal():
    connection = None
    cursor = None
    try:
        connection = psycopg2.connect(
          user="ap2204",
          password="if7fupb5",
          host="pgserver.mau.se",
          port="5432",
          database="ap2204"
        )
        cursor = connection.cursor()
        cursor.execute("SELECT MealID, MealType FROM Meals") #Hämtar ut samtliga måltidstyper från tabellen Meals
        meal_types = cursor.fetchall()
        
        if request.method == 'POST': #Om metoden sker i en POST-förfrågan, hantera formulärinmatningen från HTML-dokumentet "meal.html"
          m_id = current_user.id #Hämtar aktuella avändareID:et "m_id"
          meal_id = request.form['meal_id']
          calories = request.form['calories']
          date = request.form['date']
        
          cursor.execute("INSERT INTO MealCalories (MealID, Calories) VALUES (%s, %s) RETURNING MealCalorieID", #Infogar måltidskalorier i MealCalories-tabellen 
                        (meal_id, calories))
          meal_calorie_id = cursor.fetchone()[0]

          cursor.execute("INSERT INTO MealLog (m_id, MealCalorieID, MealDate) VALUES (%s, %s, %s)", #Infogar måltidslogg i tabellen MealLog
                        (m_id, meal_calorie_id, date))
          connection.commit() #Bekräftar ändringarna
          flash("Måltid registrerad")
          
          return redirect('/meal')
      
        return render_template('meal.html', meal_types=meal_types)
        
    except (Exception, Error) as error:
      print("Fel vid registrering av måltid:", error)
      return "Din registrering av måltiden misslyckades. Fel: {}".format(error)
    finally:
        if cursor:
          cursor.close()
        if connection:
          connection.close()
  

@app.route('/get_training_log', methods=['POST', 'GET']) #Funktion för att hämta träningslogg
@login_required
def get_training_log():
  connection = None
  cursor = None
    
  try:
      connection = psycopg2.connect(
        user="ap2204",
        password="if7fupb5",
        host="pgserver.mau.se",
        port="5432",
        database="ap2204"
      )
      cursor = connection.cursor()
      cursor.execute("SELECT ExerciseID, Name FROM Exercises") #Hämtar samtliga övningar från tabellen Exercises
      workouts = cursor.fetchall()
      
      if request.method == 'POST': #Om det sker i en POST-metod, hantera följande formulärinmatningar
        m_id = current_user.id #Hämtar det aktuella användarID:et "m_id"
        date = request.form['date']
        exercise_id = request.form['exercise_id']
        weight = request.form['weight']
        repetitions = request.form['repetitions']
        sets = request.form['sets']

        cursor.execute('INSERT INTO Workouts (m_id, Date) VALUES (%s, %s) RETURNING WorkoutID', #Infogar träningspass i tabellen Workouts
                      (m_id, date))
        workout_id =cursor.fetchone()[0]

      
        cursor.execute('INSERT INTO WorkoutDetails (WorkoutID, ExerciseID, Weight, Repetitions, Sets) VALUES (%s, %s, %s, %s, %s)', #Infogar träningsdetaljer i tabellen WorkoutDetails
                      (workout_id, exercise_id, weight, repetitions, sets))
        connection.commit() #Bekräftar ändringarna
        flash("Träningspass registrerat")
        
        return redirect('/get_training_log')
      
      return render_template('get_training_log.html', workouts=workouts)
      
  except (Exception, psycopg2.Error) as error:
        print("Fel vid inhämtning av träningsloggar:", error)
        return "Kunde inte hämta träningsloggar. Fel: {}".format(error)
  finally:
      if cursor:
        cursor.close()
      if connection:
        connection.close()

@app.route('/view_workouts') #Funktion som hämtar träningsdata från databasen
@login_required
def view_workouts():
    m_id = current_user.id  
    connection = None
    cursor = None
    try:
      connection = psycopg2.connect(
        user="ap2204",
        password="if7fupb5",
        host="pgserver.mau.se",
        port="5432",
        database="ap2204"
      )
      cursor = connection.cursor()
      #SQL-fråga för att hämta träningsdata
      query = ''' 
      SELECT Workouts.Date, Exercises.Name, WorkoutDetails.Weight, WorkoutDetails.Repetitions, WorkoutDetails.Sets
      FROM Workouts
      JOIN WorkoutDetails ON Workouts.WorkoutID = WorkoutDetails.WorkoutID
      JOIN Exercises ON WorkoutDetails.ExerciseID = Exercises.ExerciseID
      WHERE Workouts.M_id = %s
      ORDER BY Workouts.Date DESC;              
      '''
      cursor.execute(query, (m_id,)) #Utför SQL-frågan med det aktuella användarID:et "m_id"
      workouts = cursor.fetchall()
      
      return render_template('view_workouts.html', workouts=workouts) #Rendera sidan för att visa de hämtade träningspassen
    except (Exception, Error) as error:
      print("Fel vid inhämtning av träningsloggar:", error)
      return "Kunde inte hämta träningsloggar. Fel: {}".format(error)
    finally:
      if cursor:
        cursor.close()
      if connection:
        connection.close()

def authenticate_user(username, password):
    try:
        # anslut till databas
        connection = psycopg2.connect(
            user="ap2204",
            password="if7fupb5",
            host="pgserver.mau.se",
            port="5432",
            database="ap2204"
        )
      
        cursor = connection.cursor()
        #Hämtar ID, användarnamn & lösenord från en användare med ett användarnamn som matats in
        sql_query = "SELECT m_id, username, password FROM members WHERE username = %s" 
        cursor.execute(sql_query, (username,))
        user_info = cursor.fetchone()
        
        # om inget resultat hittades, returnera None
        if user_info is None:
            return None
          
        if user_info[2] == password:
          return {'m_id': user_info[0], 'username': user_info[1]}
        return None
            
    except (Exception, psycopg2.Error) as error:
        print("Gick ej att hämta data från databasen", error)
        return None
    finally: 
        # stäng anslutningen till databasen
        if connection:
            cursor.close()
            connection.close()


@app.route('/', methods=['GET', 'POST'])
def index():
  if request.method == 'POST':
    # Användarens inmatning
    username = request.form.get('username')
    password = request.form.get('password')

    # Försök autentisera användaren
    authenticated_user = authenticate_user(username, password)
    
    # Om autentiseringen lyckades, logga in användaren
    if authenticated_user:
      user = User(authenticated_user['m_id'], authenticated_user['username'])
      login_user(user)
      if current_user.is_authenticated:
        print("Användare inloggad:", current_user.username, current_user.get_id())
      else:
        print("Inloggning misslyckades.")
      return redirect(url_for('start'))
    
    else:
      flash('Fel användarnamn eller lösenord. Försök igen.', 'error')
    
  return render_template('index.html')

@app.route('/start') #En route för att visa startsidan
@login_required
def start():
   return render_template('start.html')
   

@app.route('/view_meals/<int:m_id>') #Funktion för att hämta måltider från en specifik användare
@login_required
def view_meals(m_id):
    try:
      connection = psycopg2.connect(
        user="ap2204",
        password="if7fupb5",
        host="pgserver.mau.se",
        port="5432",
        database="ap2204"
      )
      cursor = connection.cursor()
      #Definierar en SQL-fråga för att hämta måltidsdata
      cursor.execute('''
      SELECT Meals.Mealtype, MealLog.MealDate, MealCalories.Calories
      FROM MealLog
      JOIN MealCalories ON MealLog.MealCalorieID = MealCalories.MealCalorieID
      JOIN Meals ON MealCalories.MealID = Meals.MealID
      WHERE MealLog.m_id = %s
      ORDER BY MealLog.MealDate DESC;              
      ''', (m_id,))
      meals = cursor.fetchall() #Hämtar och bekräftar resultatet från SQL-frågan
      
      cursor.close()
      connection.close()
      
      return render_template('view_meals.html', meals=meals, user_id=m_id) #Renderar sidan för att visa måltider
    except (Exception, Error) as error:
      print("Fel vid inhämtning av måltidsloggar:", error)
      return "Kunde inte hämta måltidsloggar."
    finally:
      if connection:
        cursor.close()
        connection.close()
        
@app.route('/start', methods=['GET', 'POST']) #Funktion för att visa kaloribehov
def calculate_calories():
  calories = None
  if request.method == 'POST': #Hämtar formulärdata
    weight = request.form['weight']
    height = request.form['height']
    age = request.form['age']
    
    #Kontrollerar att vikt, längd och ålder är numeriska värden
    if not (isinstance (weight, str) and weight.isdigit())\
        or not (isinstance(height, str) and height.isdigit())\
        or not (isinstance(age, str) and age.isdigit()):
      flash("Vikt, längd och ålder måste vara numeriska värden.", "error")
      return redirect(url_for('meal'))
    
    #Konverterar strängvärden till numeriska värden
    weight = float(weight)
    height = float(height)
    age = int(age)
    
    #Hämtar kön och aktivitetsnivå från formuläret
    gender = request.form['gender']
    activity_level = int(request.form['activity_level'])
    
    #Beräknar dagligt kaloribehov
    calories = calculate_daily_calories(weight, height, age, gender, activity_level)
    
    #Renderar sidan för att visa beräknade kalorier
    return render_template('start.html', calories=calories)
  return render_template('start.html')
    
#Funktion för att beräkna BMR (Basal Metabolic Rate) baserat på vikt, längd, ålder och kön
def calculate_bmr(weight, height, age, gender): 
    #Olika formler för män och kvinnor
    if gender == 'MAN':
        return (10 * weight) + (6.25 * height) - (5 * age) + 5
    elif gender == 'KVINNA':
        return (10 * weight) + (6.25 * height) - (5 * age) - 161
    else:
        raise ValueError("Felaktig inmatning. Kön måste anges som antingen MAN eller KVINNA") #Om kön inte definierats, skriv ut ett felmeddelande
    
#Funktion för att beräkna dagliga kaloribehov baserat på BMR och aktivitetsnivå
def calculate_daily_calories(weight, height, age, gender, activity_level):
    bmr = calculate_bmr(weight, height, age, gender) #Beräknar BMR
    #Justerar BMR baserat på aktivitetsnivå
    if activity_level == 1:
        calories = bmr * 1.2
    elif activity_level == 2: 
        calories = bmr * 1.375 
    elif activity_level == 3: 
        calories = bmr * 1.55
    elif activity_level == 4: 
        calories = bmr * 1.725 
    elif activity_level == 5: 
        calories = bmr *1.9
    else:
        raise ValueError("Ogiltig aktivitetsnivå")
    return calories #Returnerar det beräknade dagliga kaloribehovet
  
#Funktion för att hitta en användare baserat på e-postadress
def find_user_by_email(email): 
  try:
      connection = psycopg2.connect(
        user="ap2204",
        password="if7fupb5",
        host="pgserver.mau.se",
        port="5432",
        database="ap2204"
      )
    
      cursor = connection.cursor()
      #Utför SQL-fråga för att hitta användare med given e-postadress
      cursor.execute("SELECT m_id, fullname, username, password, email FROM members WHERE email = %s", (email,))
      user_data = cursor.fetchone() #Hämtar resultat av SQL-frågan
      if user_data: #Om användardata hittades, skapa en användarrad i databasen och returnera den
        user = {
          'm_id': user_data[0],
          'fullname': user_data[1],
          'username': user_data[2],
          'password': user_data[3],
          'email': user_data[4]
          }
        return user
      return None #Om ingen användare hittades, returnera None
  except(Exception, psycopg2.Error) as error:
    print(f"Fel vid att hitta email: {error}")
    return None
  finally:
    cursor.close()
  
#Funktion för att återställa ett lösenord
@app.route('/reset', methods=['GET', 'POST']) 
def reset_password():
  if request.method == 'POST':
    email = request.form['email'] #Hämta angiven e-postadress från formuläret
    user = find_user_by_email(email) #Hitta användaren med den angivna e-postadressen
    if user:
      return render_template('set_new_password.html', user=user) #Om användare hittas, rendera sidan för att ange ett nytt lösenord
    else:
      flash("Det finns ingen användare med det angivna e-postadressen.", "error")
    
  return render_template('reset.html')

#Funktion för att ställa in ett nytt lösenord
@app.route('/set_new_password', methods=['POST'])
def set_new_password():
  #Hämta det nya lösenordet och användarID:et från formuläret
  new_password = request.form['new_password']
  user_id = request.form['user_id']
    
  try:
    connection = psycopg2.connect(
      user="ap2204",
      password="if7fupb5",
      host="pgserver.mau.se",
      port="5432",
      database="ap2204"
    )
    
    cursor = connection.cursor()
    #Uppdatera lösenordet för användaren med det angivna användarID:et
    cursor.execute("UPDATE members SET password = %s WHERE m_id = %s", (new_password, user_id))
    connection.commit() #Bekräfta ändringarna
    flash("Ditt lösenord har ändrats.", "success")
  except (Exception, psycopg2.Error) as error:
    print("Fel vid uppdatering av lösenord: ", error)
    flash('Kunde inte uppdatera lösenordet.', 'error')
  finally:
    if cursor:
      cursor.close()
    if connection:
      connection.close()
  
  return redirect(url_for('index')) #Omdirigera till startsidan efter att lösenordet har ändrats


@app.route('/recept') #En route till sidan recept
@login_required
def recept():
  return render_template('recept.html', title='Recept', user=current_user)

if __name__ == '__main__':
    app.run(debug=True)


