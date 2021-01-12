from flask import Flask, render_template,redirect, url_for, request, session, flash
from bson import ObjectId
from datetime import datetime
import hashlib
import time
import os
import mysql.connector
import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'januar2021'

UPLOAD_FOLDER = 'static/slike/shop'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
mydb = mysql.connector.connect(
	host="localhost",
	user="root",
	password="",
	database="projekat"
    )

@app.route('/')
@app.route('/index',methods=["POST","GET"])
def index():
	if request.method == "GET":
		return render_template("index.html")
	username = request.form['inputUsername']
	email = request.form['inputEmail']
	ime = request.form['inputIme']
	prezime = request.form['inputPrezime']
	adresa = request.form['inputAdresa']
	passhashed = hashlib.sha256(request.form['inputPassword'].encode()).hexdigest()
	confirmhashed = hashlib.sha256(request.form['inputPasswordConfirm'].encode()).hexdigest()
	if passhashed != confirmhashed:
		return "Šifre se ne poklapaju"
	mc = mydb.cursor()
	mc.execute(f"SELECT * FROM korisnici where username='{username}'")
	rez = mc.fetchall()
	if len(rez) > 0:
		flash("Korisničko ime je već zauzeto!")
		return redirect(url_for('index'))
	mc = mydb.cursor()
	mc.execute(f"INSERT INTO korisnici VALUES(null, '{username}', '{ime}', '{prezime}', '{adresa}', '{email}', '{passhashed}', 'korisnik')")
	mydb.commit()
	return render_template('prijava.html')

@app.route('/prijava',methods=["POST","GET"])
def prijava():
	if request.method == "GET":
		return render_template('prijava.html')

	username = request.form['inputUsername']
	passhashed = hashlib.sha256(request.form['inputPassword'].encode()).hexdigest()
	mc = mydb.cursor()
	mc.execute(f"SELECT * FROM korisnici where username='{username}'")
	rez = mc.fetchall()
	if len(rez) == 0:
		flash("Korisnik ne postoji")
		return redirect(url_for('prijava'))
	if rez[0][6] != passhashed:
		flash("Netačna šifra")
		return redirect(url_for('prijava'))
	session['username'] = username
	session['tip'] = rez[0][7]
	if rez[0][7] == "korisnik":
		return redirect(url_for('shop'))
	else:	
		return redirect(url_for('adminpanel'))

@app.route('/odjava')
def odjava():
	if 'username' not in session:
		return "Niste ulogovani"
	session.pop('username', None)
	session.pop('tip', None)
	return redirect('index')


@app.route('/dodajadmina' ,methods=["POST","GET"])
def dodajadmina():
	if session['tip'] != 'admin':
		return redirect("index")
	if request.method == "GET":
		return render_template('dodajadmina.html')
	username = request.form['inputUsername']
	email = request.form['inputEmail']
	ime = request.form['inputIme']
	prezime = request.form['inputPrezime']
	adresa = request.form['inputAdresa']
	passhashed = hashlib.sha256(request.form['inputPassword'].encode()).hexdigest()
	confirmhashed = hashlib.sha256(request.form['inputPasswordConfirm'].encode()).hexdigest()
	if passhashed != confirmhashed:
		return "Šifre se ne poklapaju"
	mc = mydb.cursor()
	mc.execute(f"SELECT * FROM korisnici where username='{username}'")
	rez = mc.fetchall()
	if len(rez) > 0:
		flash("Korisničko ime je već zauzeto")
		return redirect(url_for('dodajadmina'))
	
	mc = mydb.cursor()
	mc.execute(f"INSERT INTO korisnici VALUES(null, '{username}', '{ime}', '{prezime}', '{adresa}', '{email}', '{passhashed}', 'admin')")
	mydb.commit()
	flash(f"Uspešno kreiran novi admin - {username}")
	return render_template('dodajadmina.html')

@app.route('/dodajproizvod' ,methods=["POST","GET"])
def dodajproizvod():
	if session['tip'] != 'admin':
		return redirect("index")
	if request.method == "GET":
		return render_template('dodajproizvod.html')

	username = session['username']
	naziv = request.form['naziv']
	opis = request.form['opis']
	cena = request.form['cena']	
	file = request.files['slika']

	if file:
		filename = naziv + ".jpg"
		file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
		putanja = f'static/slike/shop/{filename}'
	mc = mydb.cursor()
	mc.execute(f"INSERT INTO proizvodi VALUES(null, '{naziv}', '{cena}', '{opis}', '{putanja}', '{username}')")
	mydb.commit()
	flash("Proizvod uspešno dodat")
	return render_template('dodajproizvod.html')

@app.route('/clanarine', methods=["POST","GET"])
def clanarine():
	if request.method == "GET":
		return render_template('clanarine.html')
	if 'username' in session:
		username = session['username']
		vrstatreninga = request.form['vrsta']
		lokacija = request.form['lokacija']
		brtermina = request.form['brtermina']
		datum = datetime.datetime.now().date()
		mc = mydb.cursor()
		mc.execute(f"INSERT INTO clanarine VALUES(null, '{username}', '{vrstatreninga}', '{lokacija}', '{brtermina}', '{datum}')")
		mydb.commit()
	else:
		flash("Molimo ulogujte se")
		return redirect("prijava")
	flash("Uspesno ste uplatili clanarinu")
	return render_template('clanarine.html')

@app.route('/shop')
def shop():
	mc = mydb.cursor()
	mc.execute(f"SELECT * FROM proizvodi")
	rez = mc.fetchall()
	return render_template('shop.html', proizvodi=rez)

@app.route('/korpa/')
def redirekt():
	flash("Molimo ulogujte se")
	return redirect("../prijava")

@app.route('/korpa/<username>')
def korpa(username):
	if 'username' not in session:
		return redirect('../index')
	if session['username'] != username:
		return redirect('../index')
	mc = mydb.cursor()
	mc.execute(f"SELECT * FROM korisnici WHERE username='{username}'")
	rez = mc.fetchall()
	if len(rez) == 0:
		return "Korisnik ne postoji"
	mc = mydb.cursor()
	mc.execute(f"SELECT * FROM korpa WHERE username='{username}'")
	rez = mc.fetchall()
	proizvodi = []
	ukupna_cena =0
	mc.execute(f"SELECT broj FROM korpa WHERE proizvod_id IN (SELECT id FROM proizvodi)")
	broj = mc.fetchall()
	for x in rez:
		mc = mydb.cursor()
		mc.execute(f"SELECT * FROM proizvodi WHERE id='{x[2]}'")
		p = mc.fetchall()
		proizvodi.append(p[0])
		ukupna_cena += float(p[0][2]*broj[0][0])
	if len(proizvodi) == 0:
		flash("Korpa je prazna")
		return redirect("../shop")
	return render_template("korpa.html",korpa = proizvodi,ukupno = ukupna_cena,broj=broj)

@app.route('/brisanjekorpa/<proizvodid>')
def brisanjekorpa(proizvodid):
	username = session['username']
	mc = mydb.cursor()
	mc.execute(f"DELETE FROM korpa WHERE proizvod_id='{proizvodid}'")
	mydb.commit()
	return redirect(f'/korpa/{username}')

@app.route('/dodavanjeukorpu/<proizvodid>')
def dodavanjeukorpu(proizvodid):
	if 'username' not in session:
		flash("Molimo ulogujte se")
		return redirect(url_for('prijava'))
	username = session['username']
	mc = mydb.cursor()
	mc.execute(f"SELECT * FROM korpa WHERE proizvod_id='{proizvodid}'")
	rez = mc.fetchall()
	if len(rez) == 0:
		mc = mydb.cursor()
		mc.execute(f"SELECT naziv FROM proizvodi WHERE ID = '{proizvodid}'")
		rez = mc.fetchall()
		naziv = rez[0][0]
		mc.execute(f"INSERT INTO korpa VALUES(null, '{username}', '{proizvodid}', '{naziv}', '1')")
		mydb.commit()
	else:
		mc = mydb.cursor()
		mc.execute(f"UPDATE korpa SET broj = broj + 1 WHERE proizvod_id='{proizvodid}'")
		mydb.commit()
	return redirect(url_for('shop'))

@app.route('/brisanje/<proizvodid>')
def brisanjeproizvoda(proizvodid):
	if session['tip'] == 'admin':
		mc = mydb.cursor()
		mc.execute(f"SELECT slika FROM proizvodi WHERE id={proizvodid}")
		slika = mc.fetchall()
		os.remove(slika[0][0])
		mc.execute(f"DELETE FROM proizvodi WHERE id={proizvodid}")
		mydb.commit()
	return redirect(url_for('shop'))

@app.route('/info')
def info():
	return render_template('info.html')

@app.route('/adminpanel')
def adminpanel():
	if session['tip'] != 'admin':
		return redirect("index")
	mc = mydb.cursor(buffered=True)
	mc.execute("SELECT * FROM clanarine")
	rez = mc.fetchall()
	mc.execute("SELECT * FROM korisnici")
	k = mc.fetchall()
	return render_template('adminpanel.html', clanarine=rez, korisnici=k)

@app.route('/profil/<username>')
def profil(username):
	if session['username'] != username:
		return redirect('../index')
	mc = mydb.cursor(buffered=True)
	mc.execute(f"SELECT * FROM korisnici WHERE username='{username}'")
	rez = mc.fetchall()
	if len(rez) == 0:
		return "Korisnik ne postoji"
	mc = mydb.cursor(buffered=True)
	mc.execute(f"SELECT * FROM clanarine WHERE username='{username}'")
	clanarine = mc.fetchall()
	mc = mydb.cursor(buffered=True)
	mc.execute(f"SELECT * FROM porudzbenice WHERE username='{username}'")
	porudzbenice = mc.fetchall()
	return render_template('profil.html', clanarine=clanarine, porudzbenice=porudzbenice)

@app.route('/brisanje')
def brisanje():
	username = session['username']
	session.pop('username', None)
	session.pop('tip', None)
	mc = mydb.cursor()
	mc.execute(f"SELECT * FROM korisnici WHERE username='{username}'")
	rez = mc.fetchall()
	if len(rez) == 0:
		return "Korisnik ne postoji"
	a = mydb.cursor()
	a.execute(f"DELETE FROM korisnici WHERE username='{username}'")
	mydb.commit()
	return redirect(url_for('index'))

@app.route('/kupovina/<username>')
def kupovina(username):
	if session['username'] != username:
		return redirect('../index')
	username = session['username']
	mc = mydb.cursor()
	mc.execute(f"SELECT * FROM korisnici WHERE username='{username}'")
	rez = mc.fetchall()
	if len(rez) == 0:
		return "Korisnik ne postoji"
	datum = datetime.datetime.now().date()
	adresa = rez[0][4]
	mc = mydb.cursor()
	mc.execute(f"INSERT INTO porudzbenice (username, proizvod_id, proizvod_naziv, broj, datum, adresa) SELECT username, proizvod_id, proizvod_naziv, broj, '{datum}', '{adresa}' FROM korpa WHERE username = '{username}'")
	mc = mydb.cursor()
	mc.execute(f"DELETE FROM korpa WHERE username = '{username}'")
	mydb.commit()
	return redirect(f'../profil/{username}')

@app.route('/porudzbenice')
def porudzbenice():
	if session['tip'] != 'admin':
		return redirect("index")
	mc = mydb.cursor()
	mc.execute("SELECT * FROM porudzbenice")
	rez = mc.fetchall()
	return render_template('porudzbenice.html', porudzbenice=rez)

@app.route('/obrisikorisnika/<username>')
def obrisikorisnika(username):
	if session['tip'] != 'admin':
		return redirect("index")
	mc = mydb.cursor()
	mc.execute(f"SELECT * FROM korisnici WHERE username='{username}'")
	rez = mc.fetchall()
	if len(rez) == 0:
		return "Korisnik ne postoji"
	a = mydb.cursor()
	a.execute(f"DELETE FROM korisnici WHERE username='{username}'")
	mydb.commit()
	return redirect(url_for('../adminpanel'))

@app.route('/izmena',methods=["POST","GET"])
def izmena():
	if request.method == "GET":
		username = session['username']
		mc = mydb.cursor()
		mc.execute(f"SELECT * FROM korisnici WHERE username='{username}'")
		rez = mc.fetchall()
		return render_template("izmena.html", korisnik=rez)
	username = session['username']
	ime = request.form['ime']
	prezime = request.form['prezime']
	adresa = request.form['adresa']
	passhashed = hashlib.sha256(request.form['sifra'].encode()).hexdigest()
	mc = mydb.cursor()
	mc.execute(f"SELECT sifra FROM korisnici where username='{username}'")
	rez = mc.fetchall()
	if passhashed != rez[0][0]:
		flash("Šifre se ne poklapaju")
		username = session['username']
		mc = mydb.cursor()
		mc.execute(f"SELECT * FROM korisnici WHERE username='{username}'")
		rez = mc.fetchall()
		return render_template("izmena.html", korisnik=rez)
	mc = mydb.cursor()
	mc.execute(f"UPDATE korisnici SET ime = '{ime}', prezime = '{prezime}', adresa = '{adresa}' WHERE username='{username}'")
	mydb.commit()
	return redirect(f"profil/{username}")

@app.route('/izmenasifre',methods=["POST","GET"])
def izmenasifre():
	if request.method == "GET":
		return render_template("izmenasifre.html")
	username = session['username']
	trenutna = hashlib.sha256(request.form['trenutnasifra'].encode()).hexdigest()
	nova = hashlib.sha256(request.form['novasifra'].encode()).hexdigest()
	novaconfirm = hashlib.sha256(request.form['potvrdanove'].encode()).hexdigest()
	mc = mydb.cursor()
	mc.execute(f"SELECT sifra FROM korisnici where username='{username}'")
	rez = mc.fetchall()
	if trenutna != rez[0][0]:
		flash("Trenutna šifra nije tačna")
		return render_template("izmenasifre.html")
	if nova != novaconfirm:
		flash("Šifre se ne poklapaju")
		return render_template("izmenasifre.html")
	mc = mydb.cursor()
	mc.execute(f"UPDATE korisnici SET sifra = '{nova}' WHERE username='{username}'")
	mydb.commit()
	flash("Šifra uspešno promenjena")
	return render_template("izmenasifre.html")

	
if __name__ == '__main__':
	app.run(debug=True)