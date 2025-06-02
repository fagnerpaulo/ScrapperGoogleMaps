from flask import Blueprint, render_template, request, jsonify
from coletardadosgooglemaps.scraper import GoogleMapsScraper
import os

# Cria um Blueprint. O primeiro argumento é o nome do Blueprint,
# o segundo é o nome do módulo onde o Blueprint está definido.
main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    """Rota para servir a página HTML principal."""
    return render_template('index.html')

@main_bp.route('/run_script', methods=['POST'])
def run_script():
    """
    Rota para receber os dados da pesquisa, executar o scraper e retornar o resultado.
    """
    data = request.get_json()
    estado = data.get('estado', '').strip()
    cidade = data.get('cidade', '').strip()
    bairro = data.get('bairro', '').strip()
    servico = data.get('servico', '').strip()

    if not all([servico, cidade, estado]):
        return jsonify({'error': 'Os campos Serviço, Cidade e Estado são obrigatórios.'}), 400

    scraper = None
    try:
        scraper = GoogleMapsScraper()
        dados_extraidos = scraper.scrape_Maps(servico, bairro, cidade, estado)

        if dados_extraidos:
            csv_path = scraper.save_to_csv(dados_extraidos, servico, cidade)
            print(f'\nBusca finalizada. Dados salvos em {csv_path}')
            return jsonify({'message': f'Pesquisa concluída! Encontrados {len(dados_extraidos)} resultados. O arquivo "{os.path.basename(csv_path)}" foi gerado na pasta data/.'}), 200
        else:
            return jsonify({'message': 'Pesquisa concluída, mas nenhum dado foi extraído.'}), 200

    except Exception as e:
        print(f"Erro geral no script de automação: {e}")
        return jsonify({'error': f'Ocorreu um erro durante a execução da pesquisa: {e}'}), 500
    finally:
        if scraper:
            scraper.quit_driver()