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



@app.route('/meal.html', methods=['POST', 'GET'])
def meal():
    if request.method == 'POST':
      m_id = request.form['m_id']
      meal_id = request.form['meal_id']
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
            "INSERT INTO meal (m_id, meal_id, calories_per_meal, date) VALUES (%s, %s, %s, %s)",
            (m_id, meal_id,calories_per_meal, date)
         )

          connection.commit()
          print("Din måltid registrerades")
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
      cursor.execute('INSERT INTO Workouts (M_id, Date, ExerciseID, Weight, Repetitions, Sets) VALUES (%s, %s, %s, %s, %s, %s)',
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

if __name__ == '__main__':
   app.run(debug=True)
    
    
