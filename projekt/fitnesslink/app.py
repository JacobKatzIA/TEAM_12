import psycopg2
from psycopg2 import Error
from flask import Flask, render_template, request, redirect, url_for, session

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

        cursor.execute("INSERT INTO members (m_id, fullname, username, password, email) VALUES (%s, %s, %s, %s, %s)",
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
    

@app.route('/register_user')
def register_user():
  return render_template('register_user.html')

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
            "INSERT INTO meal (meal_id, m_id, calories_per_meal, date) VALUES (%s, %s, %s, %s)",
            (meal_id, m_id, calories_per_meal, date)
         )
          connection.commit()
          print("Din måltid registrerades korrekt")
          return redirect('/meal')
      except (Exception, Error) as error:
         print("Fel vid registrering av måltid:", error)
         return "Din registrering av måltiden misslyckades"
      finally:
         if connection:
            cursor.close()
            connection.close()
      
    return render_template('meal.html')
  
@app.route('/get_training_log', methods=['POST', 'GET'])
def get_training_log():
  if request.method == 'POST':
    m_id = request.form['m_id']
    date = request.form['date']
    exercise_id = request.form['exercise_id']
    weight = request.form['weight']
    repetitions = request.form['repetitions']
    sets = request.form['sets']
    
    connection = None
    try:
      connection = psycopg2.connect(
        user="ap2204",
        password="if7fupb5",
        host="pgserver.mau.se",
        port="5432",
        database="ap2204"
      )
      cursor = connection.cursor()

      cursor.execute('INSERT INTO Workouts (m_id, Date) VALUES (%s, %s) RETURNING WorkoutID',
                     (m_id, date))
      workout_id =cursor.fetchone()[0]

      
      cursor.execute('INSERT INTO WorkoutDetails (WorkoutID, ExerciseID, Weight, Repetitions, Sets) VALUES (%s, %s, %s, %s, %s)',
                     (workout_id, exercise_id, weight, repetitions, sets))
      connection.commit()
      
    except (Exception, psycopg2.Error) as error:
        print("Fel vid inhämtning av träningsloggar:", error)
        return "Kunde inte hämta träningsloggar. Fel: {}".format(error)
    finally:
      if connection:
        cursor.close()
        connection.close()
      return redirect('/get_training_log')
      
  else:
    return render_template('get_training_log.html', workouts=None)

@app.route('/view_workouts/<int:m_id>')
def view_workouts(m_id):
    try:
      connection = psycopg2.connect(
        user="ap2204",
        password="if7fupb5",
        host="pgserver.mau.se",
        port="5432",
        database="ap2204"
      )
      cursor = connection.cursor()
      cursor.execute('''
      SELECT Workouts.Date, Exercises.Name, WorkoutDetails.Weight, WorkoutDetails.Repetitions, WorkoutDetails.Sets
      FROM Workouts
      JOIN WorkoutDetails ON Workouts.WorkoutID = WorkoutDetails.WorkoutID
      JOIN Exercises ON WorkoutDetails.ExerciseID = Exercises.ExerciseID
      WHERE Workouts.M_id = %s
      ORDER BY Workouts.Date DESC;              
      ''', (m_id,))
      workouts = cursor.fetchall()
      
      cursor.close()
      connection.close()
      
      return render_template('view_workouts.html', workouts=workouts, m_id=m_id)
    except (Exception, Error) as error:
      print("Fel vid inhämtning av träningsloggar:", error)
      return "Kunde inte hämta träningsloggar."
    finally:
      if connection:
        cursor.close()
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
        sql_query = "SELECT username, password FROM members WHERE username = %s AND password = %s"
        cursor.execute(sql_query, (username, password))
        user_info = cursor.fetchone()
        
        # om inget resultat hittades, returnera None
        if user_info is None:
            return None
        return {'username': user_info[0]}
            
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
        return redirect(url_for('start'))
    
    else:
        return "Fel användarnamn eller lösenord. Försök igen."
  else:
     return render_template('index.html')

@app.route('/start')
def start():
   return render_template('start.html')
   

@app.route('/view_meals/<int:m_id>')
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
      cursor.execute('''
      SELECT Meal.meal_id, Meal.m_id, Meal.calories_per_meal, Meal.date
      FROM Meal
      WHERE Meal.M_id = %s
      ORDER BY Meal.Date DESC;              
      ''', (m_id,))
      meal = cursor.fetchall()
      
      cursor.close()
      connection.close()
      
      return render_template('view_meals.html', meal=meal, m_id=m_id)
    except (Exception, Error) as error:
      print("Fel vid inhämtning av träningsloggar:", error)
      return "Kunde inte hämta träningsloggar."
    finally:
      if connection:
        cursor.close()
        connection.close()


if __name__ == '__main__':
    app.run(debug=True)


