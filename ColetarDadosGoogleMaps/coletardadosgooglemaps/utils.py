from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By # Importe By aqui se for usar na função

def safe_find_text(driver, by, value, attribute=None, wait_time=10):
    """
    Função auxiliar para encontrar um elemento com segurança e extrair seu texto ou atributo.
    Retorna 'N/A' se o elemento não for encontrado.
    """
    try:
        el = WebDriverWait(driver, wait_time).until(EC.presence_of_element_located((by, value)))
        return el.get_attribute(attribute) if attribute else el.text
    except:
        return # 'N/A'

def scroll_results(driver):
    """Realiza o scroll na lista de resultados do Google Maps."""
    import time # Importa time aqui, pois é usado apenas nesta função
    try:
        scrollable_div = WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.XPATH, '//div[contains(@aria-label, "Resultados para")]'))
        )
        for _ in range(10): # Ajuste o número de scrolls conforme a necessidade
            driver.execute_script("arguments[0].scrollTo(0, arguments[0].scrollHeight);", scrollable_div)
            time.sleep(2)
    except Exception as e:
        print(f"Erro ao rolar os resultados: {e}")