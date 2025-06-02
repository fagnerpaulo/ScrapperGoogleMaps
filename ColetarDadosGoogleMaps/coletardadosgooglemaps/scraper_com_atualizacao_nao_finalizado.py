# scraper.py
'''
Quando o Googloe encontra apenas 1 resultado na pesquisa, ele automaticamente abre a página do estabelecimento, sem passar pela coleta de links, isso gera um erro no código original, que não identifica esse "pulo".

Este novo script inclui uma atualização que contorna esta falha, porém não funcionou exatamente da maneira que eu gostaria e pensando friamente, não faz sentido eu fazer um scrape para apenas 1 resultado, então não dei sequência nesta atualização.
'''

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time
import pandas as pd
import os

# Importa as funções utilitárias
from utils import safe_find_text, scroll_results


class GoogleMapsScraper:
    def __init__(self):
        """Inicializa o WebDriver do Chrome."""
        self.driver = self._initialize_driver()

    def _initialize_driver(self):
        """Tenta inicializar o ChromeDriver, atualizando-o se necessário."""
        try:
            driver = webdriver.Chrome()
            print("ChromeDriver já está atualizado e no PATH ou é compatível.")
            return driver
        except Exception as e:
            print(f"Erro ao iniciar o ChromeDriver diretamente: {e}. Tentando atualizar...")
            try:
                driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
                print("ChromeDriver atualizado e iniciado com sucesso.")
                return driver
            except Exception as e_nested:
                raise Exception(
                    f'Não foi possível inicializar o navegador. Verifique a instalação do Chrome e do ChromeDriver: {e_nested}')

    def _extract_single_establishment_data(self):
        """
        Função auxiliar para extrair dados quando já estamos na página de um único estabelecimento.
        Retorna um dicionário com os dados.
        """
        try:
            # Espera os dados principais aparecerem na página do estabelecimento
            WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'div.m6QErb.WNBkOb.XiKgde'))
            )
            time.sleep(5)  # Um tempo adicional para a página carregar completamente

            nome = safe_find_text(self.driver, By.CSS_SELECTOR, 'h1.DUwDvf')

            nota = safe_find_text(self.driver, By.CSS_SELECTOR, 'span.MW4etd')
            # Tenta refrescar se a nota estiver vazia (com limite de tentativas)
            attempts = 0
            while not nota:
                print(f"Nota vazia, tentando atualizar... Tentativa {attempts + 1}")
                self.driver.refresh()
                time.sleep(3)
                nota = safe_find_text(self.driver, By.CSS_SELECTOR, 'span.MW4etd')
                attempts += 1

            reviews = str(safe_find_text(self.driver, By.CSS_SELECTOR, 'span.UY7F9'))
            endereco = safe_find_text(self.driver, By.CSS_SELECTOR, '[data-item-id="address"]')
            endereco = endereco.split('\n')[1] if '\n' in endereco else endereco
            telefone = safe_find_text(self.driver, By.CSS_SELECTOR, 'button[data-item-id^="phone"]')
            telefone = telefone.replace('Telefone: ', '') if telefone != 'N/A' else telefone
            telefone = telefone.split('\n')[1] if '\n' in telefone else telefone
            site = safe_find_text(self.driver, By.CSS_SELECTOR, 'a[data-item-id^="authority"]', 'href')

            print(
                f"Extraído: {nome} | Nota: {nota} | Avaliações: {reviews} | Endereço: {endereco} | Telefone: {telefone} | Site: {site}")

            return {
                'nome': nome,
                'nota': nota,
                'avaliacoes': reviews,
                'endereco': endereco,
                'telefone': telefone,
                'site': site
            }

        except Exception as e:
            print(f"Erro ao extrair dados do estabelecimento único: {e}")
            return None  # Retorna None se houver um erro na extração

    def scrape_Maps(self, servico, bairro, cidade, estado):
        """
        Executa a raspagem de dados no Google Maps com base nos parâmetros fornecidos.
        Retorna uma lista de dicionários com os dados extraídos.
        """
        pesquisa_params = [p for p in [servico, bairro, cidade, estado] if p]
        pesquisa = ", ".join(pesquisa_params).replace(' ', '+').replace(',,', ',')

        self.driver.get(f"http://google.com/maps/search/{pesquisa}")

        dados_extraidos = []

        # --- NOVA LÓGICA PARA LIDAR COM REDIRECIONAMENTO DE RESULTADO ÚNICO ---
        try:
            # Tenta esperar por elementos da lista de resultados (curto timeout)
            WebDriverWait(self.driver, 5).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, '.hfpxzc')))
            # Se chegamos aqui, provavelmente estamos na página de resultados da lista
            print("Página de resultados da lista detectada.")

            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)  # Give time for any lazy-loaded content to appear

            # Utiliza a função utilitária para rolar
            scroll_results(self.driver)

            # Coleta links da lista
            lista_itens = self.driver.find_elements(By.CSS_SELECTOR, '.hfpxzc')
            links = [el.get_attribute('href') for el in lista_itens if el.get_attribute('href')]
            print(f"Encontrados {len(links)} resultados na lista.")

            # Visita cada link da lista
            for i, link in enumerate(links):
                print(f"\nAcessando {i + 1}/{len(links)}: {link}")
                self.driver.get(link)
                data = self._extract_single_establishment_data()
                if data:
                    dados_extraidos.append(data)

        except Exception as e:
            # Se a espera por .hfpxzc falhou, é provável que fomos redirecionados
            print(f"Não foi possível encontrar elementos da lista de resultados (.hfpxzc) ou ocorreu um erro: {e}")
            print("Assumindo que fomos redirecionados para a página de um único estabelecimento.")

            # Verifica se já estamos na página de um estabelecimento único
            # Tentando encontrar o elemento de nome do estabelecimento
            try:
                WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'h1.DUwDvf')))
                print("Elemento de nome do estabelecimento detectado. Extraindo dados...")
                data = self._extract_single_establishment_data()
                if data:
                    dados_extraidos.append(data)
                else:
                    print("Nenhum dado pôde ser extraído da página do estabelecimento único.")
            except Exception as inner_e:
                print(f"Não foi possível detectar a página de um estabelecimento único. Erro: {inner_e}")
                print(
                    "A página atual não parece ser uma lista de resultados nem uma página de estabelecimento único reconhecível.")

        # --- FIM DA NOVA LÓGICA ---

        return dados_extraidos

    def save_to_csv(self, data, servico, cidade):
        """Salva os dados extraídos em um arquivo CSV na pasta 'data/'."""
        if not os.path.exists('data'):
            os.makedirs('data')  # Cria a pasta 'data' se não existir

        df = pd.DataFrame(data)
        csv_filename = f'data/resultados_Maps_{servico}_{cidade}.csv'
        df.to_csv(csv_filename, index=False, sep=';', encoding='utf-8-sig')
        return csv_filename

    def quit_driver(self):
        """Fecha o navegador."""
        if self.driver:
            self.driver.quit()