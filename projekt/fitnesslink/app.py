import psycopg2
from psycopg2 import Error
from flask import Flask, render_template, request, redirect

app = Flask(__name__)

def register_member(fullname, username, password, email):
    try:
        connection = psycopg2.connect(
          user="ap2204",
          password="if7fupb5",
          host="pgserver.mau.se",
          port="5432",
          database="ap2204")
      
        cursor = connection.cursor()

        cursor.execute("SELECT * FROM members WHERE email = %s", (email,))
        if cursor.fetchone() is not None:
            print("Användaren finns redan registrerad")
            return False
      
        cursor.execute("SELECT MAX(m_id) FROM members")
        latest_id = cursor.fetchone()[0]

        if latest_id is None:
          latest_id = 0

        next_id = latest_id + 1

        cursor.execute("INSERT INTO members (m_id, fullname, password, email) VALUES (%s, %s, %s, %s, %s)",
                      (next_id, fullname, username, password, email))
      
        connection.commit()
        print("Användare registrerad")
        return True

    except (Exception, Error) as error:
        print("Fel vid registrering:", error)
        return False
    finally:
        if connection:
           cursor.close()
           connection.close()
    

@app.route('/')
def index():
  return render_template('index.html')

@app.route('/submit', methods=['POST'])
def submit():
    fullname = request.form['fullname']
    username = request.form['username']
    password = request.form['password']
    email = request.form['email']
    if register_member(fullname, username, password, email):
       return redirect('/')
    else:
       return "Registrering misslyckades"



@app.route('/meal', methods=['GET', 'POST'])
def meal():
    if request.method == 'POST':
      meal_id = request.form['meal_id']
      m_id = request.form['m_id']
      calories_per_meal = request.form['calories_per_meal']
      date = request.form['date']
      meal_type_id = request.form['meal_type_id']

      try:
          connection = psycopg2.connect(
            user="ap2204",
            password="if7fupb5",
            host="pgserver.mau.se",
            port="5432",
            database="ap2204"
         )
          cursor = connection.cursor()

          cursor.execute(
            "INSERT INTO meal (meal_id, m_id, calories_per_meal, date, meal_type_id) VALUES (%s, %s, %s, %s, %s)",
            (meal_id, m_id, calories_per_meal, date, meal_type_id)
         )

          connection.commit()
          print("Din måltid registrerades korrekt")
          return redirect('/')
      except (Exception, Error) as error:
         print("Fel vid registrering av måltid:", error)
         return "Din registrering av måltiden misslyckades"
      finally:
         if connection:
            cursor.close()
            connection.close()
      
    return render_template('meal.html')
  
@app.route('/get_training_log', methods=['GET', 'POST'])
def get_training_log():
  if request.method == 'POST':
    m_id = request.form['m_id']
    date = request.form['date']
    exercise_id = request.form['exercise_id']
    weight = request.form['weight']
    repetitions = request.form['repetitions']
    sets = request.form['sets']
    
    try:
      connection = psycopg2.connect(
        user="ap2204",
        password="if7fupb5",
        host="pgserver.mau.se",
        port="5432",
        database="ap2204"
      )
      cursor = connection.cursor()
      cursor.execute('INSERT INTO Workoutdetails (M_id, Date, ExerciseID, Weight, Repetitions, Sets) VALUES (%s, %s, %s, %s, %s, %s)',
                     (m_id, date, exercise_id, weight, repetitions, sets))
      connection.commit()
      cursor.close()
      connection.close()
      return redirect('/get_training_log')
      
    except (Exception, Error) as error:
      print("Fel vid inhämtning av träningsloggar:", error)
      return "Kunde inte hämta träningsloggar."
    finally:
      if connection:
        cursor.close()
        connection.close()
  else:
    try:
      connection = psycopg2.connect(
        user="ap2204",
        password="if7fupb5",
        host="pgserver.mau.se",
        port="5432",
        database="ap2204"
      )
      cursor = connection.cursor()
      cursor.execute('SELECT * FROM Workouts JOIN Members ON Workouts.m_id = members.m_id;')
      workouts = cursor.fetchall()
      cursor.close()
      connection.close()
      return render_template('get_training_log.html', workouts=workouts)
      
    except (Exception, Error) as error:
      print("Fel vid inhämtning av träningsloggar:", error)
      return "Kunde inte hämta träningsloggar."
    finally:
      if connection:
        cursor.close()
        connection.close()


def connect_to_database():
    try:
        # anslut till databas
        connection = psycopg2.connect(
            user="ap2204",
            password="if7fuph5",
            host="pgserver.mau.se",
            port="5432",
            database="ap2204"
        )
        return connection
    except(Exception, psycopg2.Error) as error:
        print("Anslutningen till PostgreSQL misslyckades", error)
        return None

def authenticate_user(username_or_email, password):
    connection = connect_to_database()
    if connection is None:
        return None
      
    try: 
        cursor = connection.cursor()
        sql_query = "SELECT username, email, password FROM users WHERE username = %s OR email = %s"
        cursor.execute(sql_query, (username_or_email, username_or_email))
        user_info = cursor.fetchone()
        
        # om inget resultat hittades, returnera None
        if user_info is None:
            return None

        if password == user_info[2]:
            return {'username': user_info[0], 'email': user_info[1]}
        else: 
            return None
    except (Exception, psycopg2.Error) as error:
        print("Gick ej att hämta data från databasen", error)
        return None
    finally: 
        # stäng anslutningen till databasen
        if connection:
            cursor.close()
            connection.close()

app = Flask(__name__)

@app.route('/Login')
def login():
    # Användarens inmatning
    input_username_or_email = input("Ange användarnamn eller e-post: ")
    input_password = input("Ange lösenord: ")

    # Försök autentisera användaren
    authenticated_user = authenticate_user(input_username_or_email, input_password)
    
    # Om autentiseringen lyckades, logga in användaren
    if authenticated_user:
        return f"Välkommen {authenticated_user['username']}! Du är nu inloggad."
    else:
        return "Fel användarnamn, e-post eller lösenord. Försök igen."
    
if __name__ == '__main__':
    app.run(debug=True)


