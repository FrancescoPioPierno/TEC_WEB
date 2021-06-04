from flask import redirect, render_template, url_for, flash, request, session, current_app
from shop import db, app, photos, bcrypt, login_manager
from flask_login import login_required, current_user, logout_user, login_user
from .forms import CustomerRegisterForm, CustomerLoginForm
from .models import Register, CustomerOrder
import secrets, os

@app.route('/customerregister', methods=['GET', 'POST'])
def customer_register():
    form = CustomerRegisterForm()
    if form.validate_on_submit():
        hash_password = bcrypt.generate_password_hash(form.password.data)
        register = Register(name=form.name.data, username=form.username.data, email=form.email.data,
                            password=hash_password, country=form.country.data,  contact=form.contact.data,
                            city=form.city.data, address=form.address.data, zipcode=form.zipcode.data)
        db.session.add(register)
        flash(f'Benvenuto {form.name.data} Grazie per esserti registrato', 'success')
        db.session.commit()
        return redirect(url_for('login'))


    return render_template('customer/register.html', form=form)

@app.route('/customer/login', methods=['GET', 'POST'])
def customerLogin():
    form = CustomerLoginForm()
    if form.validate_on_submit():
        user = Register.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user)
            flash('Sei connesso ora!', 'success')
            next = request.args.get('next')
            return redirect(next or url_for('home'))
        flash('Email e password incorrette', 'danger')
        return redirect(url_for('customerLogin'))



    return render_template('customer/login.html', form=form)


@app.route('/customer/logout')
def customer_logout():
    logout_user()
    return redirect(url_for('home'))

@app.route('/getorder')
@login_required
def get_order():
    if current_user.is_authenticated:
        customer_id = current_user.id
        invoice = secrets.token_hex(5)
        try:
            order = CustomerOrder(invoice=invoice, customer_id=customer_id, orders=session['Shoppingcart'])
            db.session.add(order)
            db.session.commit()
            session.pop('Shoppingcart')
            flash('Il tuo ordine è stato inviato', 'success')
            return redirect(url_for('orders', invoice=invoice))

        except Exception as e:
            print(e)
            flash('Qualcosa è andato storto', 'danger')
            return redirect(url_for('getCart'))

@app.route('/orders/<invoice>')
@login_required
def orders(invoice):
    if current_user.is_authenticated:
        grandTotal = 0
        subTotal = 0
        customer_id = current_user.id
        customer = Register.query.filter_by(id=customer_id).first()
        orders = CustomerOrder.query.filter_by(customer_id=customer_id).order_by(CustomerOrder.id.desc()).first()
        for _key, product in orders.orders.items():
            discount = (product['discount']/100)*float(product['price'])
            subTotal += float(product['price']) * int(product['quantity'])
            subTotal -= discount
            tax = ("%.2f" % (.06 * float(subTotal)))
            grandTotal = float("%.2f" % (1.06 * subTotal))
    else:
        return redirect(url_for('customerLogin'))

    return render_template('customer/order.html', invoice=invoice, tax=tax, subTotal=subTotal, grandTotal=grandTotal,
                           customer=customer, orders=orders)
