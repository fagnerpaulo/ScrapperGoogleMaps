from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time
import pandas as pd
import os # Para criar a pasta 'data' se não existir

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
                raise Exception(f'Não foi possível inicializar o navegador. Verifique a instalação do Chrome e do ChromeDriver: {e_nested}')

    def scrape_Maps(self, servico, bairro, cidade, estado):
        """
        Executa a raspagem de dados no Google Maps com base nos parâmetros fornecidos.
        Retorna uma lista de dicionários com os dados extraídos.
        """
        pesquisa_params = [p for p in [servico, bairro, cidade, estado] if p]
        pesquisa = ", ".join(pesquisa_params).replace(' ', '+').replace(',,', ',')

        self.driver.get(f"http://google.com/maps/search/{pesquisa}")
        # Espera resultados aparecerem
        WebDriverWait(self.driver, 60).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, '.hfpxzc')))

        # Utiliza a função utilitária para rolar
        scroll_results(self.driver)

        # Coleta links
        lista_itens = self.driver.find_elements(By.CSS_SELECTOR, '.hfpxzc')
        links = [el.get_attribute('href') for el in lista_itens if el.get_attribute('href')]
        print(f"Encontrados {len(links)} resultados.")

        dados_extraidos = []

        # Visita cada link
        for i, link in enumerate(links):
            print(f"\nAcessando {i+1}/{len(links)}: {link}")
            self.driver.get(link)

            try:
                # Espera os dados principais aparecerem
                WebDriverWait(self.driver, 15).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, 'div.m6QErb.WNBkOb.XiKgde'))
                )
                time.sleep(5)

                # Utiliza a função utilitária para extrair dados
                nome = safe_find_text(self.driver, By.CSS_SELECTOR, 'h1.DUwDvf')
                nota = safe_find_text(self.driver, By.CSS_SELECTOR, 'span.MW4etd')

                # Tenta refrescar se a nota estiver vazia
                while not nota:
                    self.driver.refresh()
                    time.sleep(3)  # Tempo para a página recarregar
                    nota = safe_find_text(self.driver, By.CSS_SELECTOR, 'span.MW4etd')

                reviews = str(safe_find_text(self.driver, By.CSS_SELECTOR, 'span.UY7F9'))
                endereco = safe_find_text(self.driver, By.CSS_SELECTOR, '[data-item-id="address"]')
                endereco = endereco.split('\n')[1] if '\n' in endereco else endereco
                telefone = safe_find_text(self.driver, By.CSS_SELECTOR, 'button[data-item-id^="phone"]')
                telefone = telefone.replace('Telefone: ', '') if telefone != 'N/A' else telefone
                telefone = telefone.split('\n')[1] if '\n' in telefone else telefone
                site = safe_find_text(self.driver, By.CSS_SELECTOR, 'a[data-item-id^="authority"]', 'href')

                print(f"{nome} | {nota} | {reviews} | {endereco} | {telefone} | {site}")

                dados_extraidos.append({
                    'nome': nome,
                    'nota': nota,
                    'avaliacoes': reviews,
                    'endereco': endereco,
                    'telefone': telefone,
                    'site': site
                })

            except Exception as e:
                print(f"Erro ao extrair dados do item {i+1}: {e}")
                continue
        return dados_extraidos

    def save_to_csv(self, data, servico, cidade):
        """Salva os dados extraídos em um arquivo CSV na pasta 'data/'."""
        if not os.path.exists('data'):
            os.makedirs('data') # Cria a pasta 'data' se não existir

        df = pd.DataFrame(data)
        csv_filename = f'data/resultados_Maps_{servico}_{cidade}.csv'
        df.to_csv(csv_filename, index=False, sep=';', encoding='utf-8-sig')
        return csv_filename

    def quit_driver(self):
        """Fecha o navegador."""
        if self.driver:
            self.driver.quit()