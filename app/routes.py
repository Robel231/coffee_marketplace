from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, session
from flask_login import login_user, logout_user, login_required, current_user
from app import db
from app.models import User, Product, Order, CartItem
from app.forms import RegistrationForm, LoginForm, ProductForm, ProfileForm
import stripe
import os
import paypalrestsdk

bp = Blueprint('main', __name__)

# Stripe Configuration
stripe.api_key = os.getenv('STRIPE_SECRET_KEY')

@bp.route('/stripe_checkout', methods=['POST'])
@login_required
def stripe_checkout():
    cart_items = CartItem.query.filter_by(buyer_id=current_user.id).all()
    total_amount = sum(item.quantity * item.product.price for item in cart_items)

    try:
        session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'usd',
                    'product_data': {
                        'name': 'Ethiopian Coffee Order',
                    },
                    'unit_amount': int(total_amount * 100),
                },
                'quantity': 1,
            }],
            mode='payment',
            success_url=url_for('main.success', _external=True),
            cancel_url=url_for('main.cancel', _external=True),
        )
        return redirect(session.url, code=303)
    except Exception as e:
        return jsonify(error=str(e)), 500

@bp.route('/success')
def success():
    flash("Payment successful!", "success")
    return redirect(url_for('main.orders'))

@bp.route('/cancel')
def cancel():
    flash("Payment cancelled!", "danger")
    return redirect(url_for('main.cart'))

# PayPal Configuration
paypalrestsdk.configure({
    "mode": "sandbox",  # Change to "live" for production
    "client_id": os.getenv('PAYPAL_CLIENT_ID'),
    "client_secret": os.getenv('PAYPAL_SECRET')
})

@bp.route('/paypal_checkout', methods=['POST'])
@login_required
def paypal_checkout():
    cart_items = CartItem.query.filter_by(buyer_id=current_user.id).all()
    total_amount = sum(item.quantity * item.product.price for item in cart_items)

    payment = paypalrestsdk.Payment({
        "intent": "sale",
        "payer": {"payment_method": "paypal"},
        "redirect_urls": {
            "return_url": url_for('main.paypal_success', _external=True),
            "cancel_url": url_for('main.paypal_cancel', _external=True)
        },
        "transactions": [{
            "amount": {"total": f"{total_amount:.2f}", "currency": "USD"},
            "description": "Ethiopian Coffee Order"
        }]
    })

    if payment.create():
        return redirect(payment.links[1].href)  # Redirect to PayPal for approval
    else:
        return jsonify(error=payment.error), 500

@bp.route('/paypal_success')
def paypal_success():
    flash("Payment successful via PayPal!", "success")
    return redirect(url_for('main.orders'))

@bp.route('/paypal_cancel')
def paypal_cancel():
    flash("Payment cancelled via PayPal!", "danger")
    return redirect(url_for('main.cart'))

# Home Page
@bp.route('/')
def home():
    products = Product.query.all()
    return render_template('home.html', products=products)

# User Authentication
@bp.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data, role=form.role.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('main.login'))
    return render_template('register.html', form=form)

@bp.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user)
            flash('Login successful!', 'success')
            return redirect(url_for('main.home'))
        flash('Invalid email or password', 'danger')
    return render_template('login.html', form=form)

@bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('main.home'))

# Product Management
@bp.route('/add_product', methods=['GET', 'POST'])
@login_required
def add_product():
    if current_user.role != 'farmer':
        flash('You do not have permission to add products!', 'danger')
        return redirect(url_for('main.home'))
    
    form = ProductForm()
    if form.validate_on_submit():
        product = Product(
            name=form.name.data,
            description=form.description.data,
            price=form.price.data,
            farmer_id=current_user.id
        )
        db.session.add(product)
        db.session.commit()
        flash('Product added successfully!', 'success')
        return redirect(url_for('main.home'))
    
    return render_template('add_product.html', form=form)

@bp.route('/products')
def products():
    products = Product.query.all()
    return render_template('products.html', products=products)

@bp.route('/product/<int:product_id>')
def product_detail(product_id):
    product = Product.query.get_or_404(product_id)
    return render_template('product_detail.html', product=product)

# Cart Management
@bp.route('/cart')
@login_required
def cart():
    cart_items = CartItem.query.filter_by(buyer_id=current_user.id).all()
    total_price = sum(item.quantity * item.product.price for item in cart_items)
    return render_template('cart.html', cart_items=cart_items, total_price=total_price)

@bp.route('/add_to_cart/<int:product_id>', methods=['POST'])
@login_required
def add_to_cart(product_id):
    product = Product.query.get_or_404(product_id)
    quantity = int(request.form.get('quantity', 1))
    
    cart_item = CartItem.query.filter_by(buyer_id=current_user.id, product_id=product_id).first()
    if cart_item:
        cart_item.quantity += quantity
    else:
        cart_item = CartItem(buyer_id=current_user.id, product_id=product_id, quantity=quantity)
        db.session.add(cart_item)
    
    db.session.commit()
    flash('Product added to cart!', 'success')
    return redirect(url_for('main.cart'))

@bp.route('/remove_from_cart/<int:item_id>')
@login_required
def remove_from_cart(item_id):
    cart_item = CartItem.query.get_or_404(item_id)
    db.session.delete(cart_item)
    db.session.commit()
    flash('Product removed from cart!', 'success')
    return redirect(url_for('main.cart'))

# Orders
@bp.route('/orders')
@login_required
def orders():
    orders = Order.query.filter_by(buyer_id=current_user.id).all()
    return render_template('orders.html', orders=orders)

# Profile Management
@bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    form = ProfileForm()
    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.email = form.email.data
        if form.password.data:
            current_user.set_password(form.password.data)
        db.session.commit()
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('main.profile'))
    return render_template('profile.html', form=form)

# API Endpoints
@bp.route('/api/cart/count')
@login_required
def cart_count():
    count = CartItem.query.filter_by(buyer_id=current_user.id).count()
    return jsonify({'count': count})

@bp.route('/cart/update/<int:item_id>', methods=['POST'])
@login_required
def update_cart_item(item_id):
    cart_item = CartItem.query.get_or_404(item_id)
    data = request.get_json()
    cart_item.quantity = data['quantity']
    db.session.commit()
    return jsonify({'success': True})

@bp.route('/checkout', methods=['POST'])
@login_required
def checkout():
    try:
        cart_items = CartItem.query.filter_by(buyer_id=current_user.id).all()
        for item in cart_items:
            order = Order(buyer_id=current_user.id, product_id=item.product_id, quantity=item.quantity, total_price=item.quantity * item.product.price)
            db.session.add(order)
            db.session.delete(item)
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})
