from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, login_user, LoginManager, login_required, logout_user, current_user
from flask_cors import CORS

# Cria uma instância da classe Flask, representando a aplicação web em Python.
application = Flask(__name__)
application.config['SECRET_KEY'] = 'lucas'  #

# Configuração do banco de dados SQLite.
application.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///ecommerce.db'

# Inicializa a extensão Flask-Login e configura as configurações de login.
login_manager = LoginManager()
db = SQLAlchemy(application)
login_manager.init_app(application) 
login_manager.login_view = 'login'

# Habilita o Compartilhamento de Recursos de Origem Cruzada (CORS) para permitir solicitações de outros sistemas.
CORS(application)

# Modelagem do banco de dados:

# Produto (Id, nome, preço, descrição)
class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    price = db.Column(db.Float, nullable=False)
    description = db.Column(db.Text, nullable=False)
    
class CartItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)

# Usuário (id, nome de usuário, senha)
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), nullable=False, unique=True)
    password = db.Column(db.String(80), nullable=True)
    # relacionamento do usuário com o carrinho
    cart = db.relationship('CartItem', backref='user', lazy=True)

# Rotas da API:

# Cria um produto.
@application.route('/api/products/add', methods=['POST'])
@login_required
def add_product():
    data_product = request.json
    if 'name' in data_product and 'price' in data_product:
        product = Product(name=data_product['name'], price=data_product['price'], description=data_product.get('description', ''))
        db.session.add(product)
        db.session.commit()
        return jsonify({
            'mensagem': 'Produto adicionado com sucesso'
        }), 200
    return jsonify({
        'mensagem': 'Dados de produto inválidos'
    }), 400

# Deleta um produto pelo ID.
@application.route('/api/products/delete/<int:product_id>', methods=['DELETE'])
@login_required
def delete_product(product_id):
    product = Product.query.get(product_id)
    if product:
        db.session.delete(product)
        db.session.commit()
        return jsonify({
            'mensagem': 'Produto excluído'
        }), 200
    return jsonify({
        'mensagem': 'Produto não encontrado'
    }), 404

# Obtém detalhes de um produto pelo ID.
@application.route('/api/products/<int:product_id>', methods=['GET'])
def get_products_details(product_id):
    product = Product.query.get(product_id)
    if product:
        return jsonify({
            'id': product.id,
            'nome': product.name,
            'preco': product.price,
            'descricao': product.description,
        })
    return jsonify({
        'mensagem': 'Produto não encontrado'
    }), 404

# Obtém todos os produtos.
@application.route('/api/products/', methods=['GET'])
def get_all_products():
    products = Product.query.all()
    product_list = []
    for product in products:
        product_data = {
            'id': product.id,
            'nome': product.name,
            'preco': product.price,
        }
        product_list.applicationend(product_data)
    return jsonify(product_list)

# Atualiza um produto pelo ID.
@application.route('/api/products/update/<int:product_id>', methods=['PUT'])
@login_required
def update_product(product_id):
    product = Product.query.get(product_id)
    if not product:
        return jsonify({
            'mensagem': 'Produto não encontrado'
        }), 404
    product_data = request.json
    if 'nome' in product_data:
        product.name = product_data['nome']
    if 'preco' in product_data:
        product.price = product_data['preco']
    if 'descricao' in product_data:
        product.description = product_data['descricao']
    db.session.commit()
    return jsonify({
        'mensagem': 'Produto atualizado com sucesso'
    })

# Adiciona item ao carrinho.
@application.route('/api/cart/add/<int:product_id>', methods=['POST'])
@login_required
def add_to_cart(product_id):
    # Usuário
    user = User.query.get(int(current_user.id))
    # Produto
    product = Product.query.get(int(product_id))
    if user and product:
        cart_item = CartItem(user_id=user.id, product_id=product.id)
        db.session.add(cart_item)
        db.session.commit()
        return jsonify({
            'mensagem': 'Item adicionado ao carrinho com sucesso'
        })
    return jsonify({
        'mensagem': 'Falha ao adicionar item ao carrinho'
    }), 400
    
# Remove item do carrinho.
@application.route('/api/cart/remove/<int:product_id>', methods=['DELETE'])
@login_required
def remove_from_cart(product_id):
    # Produto, usuário = item no carrinho
    cart_item = CartItem.query.filter_by(user_id=current_user.id, product_id=product_id).first()
    if cart_item:
        db.session.delete(cart_item)
        db.session.commit()
        return jsonify({
            'mensagem': 'Item removido do carrinho com sucesso'
        })
    return jsonify({
        'mensagem': 'Falha ao remover item do carrinho'
    }), 400
    
# Visualiza conteúdo do carrinho.
@application.route('/api/cart', methods=['GET'])
@login_required
def view_cart():
    user = User.query.get(int(current_user.id))
    cart_items = user.cart
    cart_content = []
    for cart_item in cart_items:
        product = Product.query.get(cart_item.product_id)
        cart_content.applicationend({
            'id': cart_item.id,
            'user_id': cart_item.user_id,
            'product_id': cart_item.product_id, 
            'nome_produto': product.name,
            'preco_produto': product.price,
        })
    return jsonify(cart_content)

# Finaliza a compra e limpa o carrinho.
@application.route('/api/cart/checkout', methods=['POST'])
@login_required
def checkout():
    user = User.query.get(int(current_user.id))
    cart_items = user.cart
    for cart_item in cart_items:
        db.session.delete(cart_item)
    db.session.commit()
    return jsonify({
        'mensagem': 'Compra realizada com sucesso! Carrinho foi esvaziado'
    })
    

# Autenticação

# Função de carregamento para recuperar um usuário por ID para o Flask-Login.
#   toda vez que uma rota protegida com @login_required precisa recuperar
#   qual usuário está tentando acessar essa rota e ele faz isso usando o loader_user
#   buscado por id
###########################################
@login_manager.user_loader 
def load_user(user_id):    
    return User.query.get(int(user_id)) 
###########################################

# Rota de login.
@application.route('/login', methods=['POST'])
def login():
    data_user = request.json
    user = User.query.filter_by(username=data_user.get('username')).first()
    if user and data_user.get('password') == user.password:
        login_user(user)
        return jsonify({
            'mensagem': 'Login realizado com sucesso'
        })
    return jsonify({
        'mensagem': 'Não autorizado, credenciais inválidas'
    }), 401

# Rota de logout.
@application.route('/logout', methods=['POST'])
@login_required
def logout():
    logout_user()
    return jsonify({
        'mensagem': 'Logout realizado com sucesso'
    })

# Rota raiz (página inicial).
@application.route('/')
def hello_world():
    return 'Olá, mundo'

# Executa a aplicação em modo de depuração se este script for o principal.
if __name__ == '__main__':
    application.run(debug=True)
