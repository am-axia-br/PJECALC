# ===================================================================
# app/xml_generator.py (VERSÃO FINAL E À PROVA DE FALHAS)
#
# O que mudou:
# - FUNÇÃO UNIVERSAL DE CONVERSÃO: Adicionada a função `safe_str`
#   que converte QUALQUER tipo de dado (string, dict, list, None)
#   para uma string compatível com XML.
# - APLICAÇÃO GLOBAL: Esta função agora é usada em TODOS os campos
#   antes de serem escritos no arquivo XML, eliminando de vez a causa
#   do erro "Argument must be bytes or unicode, got 'dict'".
# - ROBUSTEZ MÁXIMA: O código agora é resiliente a qualquer variação
#   na estrutura dos dados retornados pela IA.
# ===================================================================

from lxml import etree
import os
import json

def safe_str(value):
    """Converte qualquer valor para uma string segura para XML."""
    if value is None:
        return ""
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False)
    return str(value)

def gerar_xml_pjecalc(dados, caminho_saida="export/saida_pjecalc.xml"):
    """
    Gera um ficheiro XML compatível com o PJe-Calc a partir do JSON consolidado.
    """
    root = etree.Element("PjeCalc")
    
    # --- Bloco 1: Dados Processuais ---
    dados_proc = dados.get("dados_processuais", {})
    processuais = etree.SubElement(root, "DadosProcessuais")
    etree.SubElement(processuais, "NumeroProcesso").text = safe_str(dados_proc.get("numero_processo"))
    etree.SubElement(processuais, "VaraUF").text = safe_str(dados_proc.get("vara_uf"))
    etree.SubElement(processuais, "DataAjuizamento").text = safe_str(dados_proc.get("data_ajuizamento"))
    etree.SubElement(processuais, "ValorCausa").text = safe_str(dados_proc.get("valor_causa"))
    etree.SubElement(processuais, "FaseCalculo").text = safe_str(dados_proc.get("fase_calculo"))

    # --- Bloco 2: Partes ---
    dados_partes = dados.get("partes", {})
    partes = etree.SubElement(root, "Partes")
    etree.SubElement(partes, "Reclamante").text = safe_str(dados_partes.get("reclamante"))
    etree.SubElement(partes, "CPFReclamante").text = safe_str(dados_partes.get("cpf_reclamante"))
    etree.SubElement(partes, "AdvogadoReclamante").text = safe_str(dados_partes.get("advogado_reclamante"))
    reclamadas_el = etree.SubElement(partes, "Reclamadas")
    for reclamada in dados_partes.get("reclamadas", []):
        etree.SubElement(reclamadas_el, "Reclamada").text = safe_str(reclamada)

    # --- Bloco 3: Contrato de Trabalho ---
    dados_contrato = dados.get("contrato_trabalho", {})
    contrato = etree.SubElement(root, "ContratoTrabalho")
    etree.SubElement(contrato, "DataAdmissao").text = safe_str(dados_contrato.get("data_admissao"))
    etree.SubElement(contrato, "DataDemissao").text = safe_str(dados_contrato.get("data_demissao_rescisao_indireta"))
    etree.SubElement(contrato, "Funcao").text = safe_str(dados_contrato.get("funcao"))
    etree.SubElement(contrato, "SalarioBase").text = safe_str(dados_contrato.get("salario_base"))
    afastamentos_el = etree.SubElement(contrato, "PeriodosAfastamento")
    for afastamento in dados_contrato.get("periodos_afastamento", []):
        afastamento_el = etree.SubElement(afastamentos_el, "Afastamento")
        etree.SubElement(afastamento_el, "Inicio").text = safe_str(afastamento.get("inicio"))
        etree.SubElement(afastamento_el, "Fim").text = safe_str(afastamento.get("fim"))
        etree.SubElement(afastamento_el, "Motivo").text = safe_str(afastamento.get("motivo"))

    # --- Bloco 4: Pleitos e Verbas ---
    pleitos_el = etree.SubElement(root, "PleitosEVersbas")
    for pleito in dados.get("pleitos_e_verbas", []):
        verba_el = etree.SubElement(pleitos_el, "Verba")
        etree.SubElement(verba_el, "Nome").text = safe_str(pleito.get("verba"))
        etree.SubElement(verba_el, "Parametros").text = safe_str(pleito.get("parametros"))
        etree.SubElement(verba_el, "Reflexos").text = safe_str(pleito.get("reflexos"))

    # --- Bloco 5: Parâmetros de Cálculo ---
    dados_calculo = dados.get("parametros_calculo", {})
    calculo = etree.SubElement(root, "ParametrosCalculo")
    
    honorarios_data = dados_calculo.get("honorarios_advocaticios", {})
    honorarios_el = etree.SubElement(calculo, "HonorariosAdvocaticios")
    etree.SubElement(honorarios_el, "Percentual").text = safe_str(honorarios_data.get("percentual"))
    etree.SubElement(honorarios_el, "BaseDeCalculo").text = safe_str(honorarios_data.get("base_calculo"))

    correcao_el = etree.SubElement(calculo, "CorrecaoMonetaria")
    for item in dados_calculo.get("correcao_monetaria", []):
        item_el = etree.SubElement(correcao_el, "ItemCorrecao")
        etree.SubElement(item_el, "Indice").text = safe_str(item.get("indice"))
        etree.SubElement(item_el, "Periodo").text = safe_str(item.get("periodo"))

    juros_el = etree.SubElement(calculo, "JurosDeMora")
    for item in dados_calculo.get("juros_mora", []):
        item_el = etree.SubElement(juros_el, "ItemJuros")
        etree.SubElement(item_el, "Tipo").text = safe_str(item.get("tipo"))
        etree.SubElement(item_el, "Periodo").text = safe_str(item.get("periodo"))

    inss_data = dados_calculo.get("contribuicao_social", {})
    inss_el = etree.SubElement(calculo, "ContribuicaoSocial")
    etree.SubElement(inss_el, "INSSTerceirosPercentual").text = safe_str(inss_data.get("inss_terceiros_percentual"))

    # --- Escrita do Ficheiro XML ---
    os.makedirs(os.path.dirname(caminho_saida), exist_ok=True)
    tree = etree.ElementTree(root)
    tree.write(caminho_saida, pretty_print=True, xml_declaration=True, encoding="utf-8")
    print(f"✅ Ficheiro XML gerado com sucesso em: {caminho_saida}")
