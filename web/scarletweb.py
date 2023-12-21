from flask import Flask, render_template, url_for, request, redirect, session
from flask_sqlalchemy import SQLAlchemy


app = Flask(__name__)
app.config['SECRET_KEY'] = 'scarletweb'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///scarletproduct.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.app_context().push()
db = SQLAlchemy(app)


class Size(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    value = db.Column(db.String, nullable=False)  # Например, "S", "M", "L" и т.д.

    def __repr__(self):
        return f'<Size {self.value}>'


item_size = db.Table('item_size',
    db.Column('item_id', db.Integer, db.ForeignKey('item.id'), primary_key=True),
    db.Column('size_id', db.Integer, db.ForeignKey('size.id'), primary_key=True)
)


class Item(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    image = db.Column(db.String, nullable=False)
    title = db.Column(db.String(100), nullable=False)
    sizes = db.relationship('Size', secondary=item_size, lazy='subquery',
                            backref=db.backref('items', lazy=True))
    price = db.Column(db.Integer, nullable=False)
    text = db.Column(db.Text, nullable=False)

    def repr(self):
        return f'<Item {self.title}>'


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/about')
def about():
    return render_template('about.html')


@app.route('/catalog')
def catalog():
    items = Item.query.all()
    return render_template('catalog.html', items=items)


@app.route('/addtocatalog', methods=['GET', 'POST'])
def addtocatalog():
    if request.method == 'POST':
        title = request.form['title']
        image_url = request.form['image']
        price = request.form['price']
        text = request.form['text']

        size_ids = request.form.getlist('sizes')  # получаем список id выбранных размеров
        sizes = Size.query.filter(Size.id.in_(size_ids)).all()  # получаем объекты Size

        new_item = Item(title=title, image=image_url, price=price, text=text)
        new_item.sizes.extend(sizes)  # добавляем размеры к товару

        db.session.add(new_item)
        db.session.commit()

        return redirect(url_for('addtocatalog'))

    sizes = Size.query.all()  # получаем все размеры для передачи в шаблон
    return render_template('addtocatalog.html', sizes=sizes)


@app.route('/favourite')
def favourite():
    favourite_item_ids = session.get('favourite_items', [])
    favourite_items = Item.query.filter(Item.id.in_(favourite_item_ids)).all() if favourite_item_ids else []
    items = {item.id: item for item in favourite_items}
    return render_template('favourite.html', items=items)


@app.route('/delete_item', methods=['POST'])
def delete_item():
    item_id = request.form.get('item_id')
    if item_id:
        item_to_delete = Item.query.get(item_id)
        if item_to_delete:
            db.session.delete(item_to_delete)
            db.session.commit()

        else:
            ""
    return redirect(url_for('addtocatalog'))


@app.route('/item/<int:item_id>')
def item_detail(item_id):
    item = Item.query.get_or_404(item_id)
    return render_template('item_detail.html', item=item)


@app.route('/add_to_cart/<int:item_id>', methods=['POST'])
def add_to_cart(item_id):
    if 'cart' not in session:
        session['cart'] = []
    session['cart'].append(item_id)
    session.modified = True
    return redirect(url_for('cart'))


@app.route('/cart')
def cart():
    items_in_cart = Item.query.filter(Item.id.in_(session.get('cart', []))).all()
    return render_template('cart.html', items=items_in_cart)


@app.route('/remove_from_cart/<int:item_id>', methods=['POST'])
def remove_from_cart(item_id):
    if 'cart' in session and item_id in session['cart']:
        session['cart'].remove(item_id)
        session.modified = True
    return redirect(url_for('cart'))


def add_sizes_to_db():
    if not Size.query.first():
        sizes_to_add = ['36', '37', '38', '39', '40', '41', '42', '43', '44', '45', '46', '47']
        for size_value in sizes_to_add:
            size = Size(value=size_value)
            db.session.add(size)
        db.session.commit()


add_sizes_to_db()


@app.route('/toggle_favourite/<int:item_id>', methods=['POST'])
def toggle_favourite(item_id):
    favourite_items = session.get('favourite_items', [])

    if item_id in favourite_items:
        favourite_items.remove(item_id)
    else:
        favourite_items.append(item_id)

    session['favourite_items'] = favourite_items
    session.modified = True

    return favourite(favourite_items=favourite_items)


if __name__ == "__main__":
    app.run(debug=True)