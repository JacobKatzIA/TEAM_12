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

@app.route('\submit', methods=['POST'])
def submit():
    fullname = request.form['fullname']
    username = request.form['username']
    password = request.form['password']
    email = request.form['email']
    if register_member(fullname, username, password, email):
       return redirect('/')
    else:
       return "Registrering misslyckades"



@app.route('\meal', methods=['GET', 'POST'])
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

if __name__ == '__main__':
   app.run(debug=True)
    
    
