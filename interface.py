# ===================================================================
# app/interface.py (VERSÃO COM FORMATAÇÃO PROFISSIONAL E DEFINITIVA)
#
# O que mudou:
# - FUNÇÃO DE FORMATAÇÃO: Adicionada a nova função `formatar_parametros`
#   que converte de forma inteligente os parâmetros (sejam strings,
#   listas ou dicionários) em um texto claro e legível.
# - APRESENTAÇÃO APRIMORADA: A tabela de "Pleitos e Verbas" agora
#   usa essa função para pré-formatar os dados antes de exibi-los,
#   resolvendo o problema de formatação e melhorando a experiência
#   do usuário.
# - ESTABILIDADE: O código mantém a estrutura de máquina de estados
#   robusta e o tratamento de erros aprimorado.
# ===================================================================

import streamlit as st
import os
import json
import traceback
import pandas as pd
from ocr import aplicar_ocr
from extrator import dividir_em_chunks, extrair_dados_parciais, consolidar_resultados
from xml_generator import gerar_xml_pjecalc
from exportador_docx import gerar_docx_resumo

# --- CONFIGURAÇÃO DA PÁGINA E ESTADO INICIAL ---

st.set_page_config(page_title="PJe-Calc Automático com IA", layout="wide")

def inicializar_estado():
    """Define o estado inicial da aplicação se não existir."""
    if "estado_app" not in st.session_state:
        st.session_state.estado_app = "inicial"
    # ... (demais inicializações de estado)
    if "dados_completos" not in st.session_state:
        st.session_state.dados_completos = None
    if "log_detalhado" not in st.session_state:
        st.session_state.log_detalhado = None
    if "error_message" not in st.session_state:
        st.session_state.error_message = None
    if "error_details" not in st.session_state:
        st.session_state.error_details = None

def reiniciar_analise():
    """Limpa o session_state e reseta a aplicação para o estado inicial."""
    keys_to_clear = list(st.session_state.keys())
    for key in keys_to_clear:
        del st.session_state[key]
    
    temp_pdf_path = os.path.join("export", "temp.pdf")
    if os.path.exists(temp_pdf_path):
        os.remove(temp_pdf_path)
    
    inicializar_estado()

# --- FUNÇÕES DE LÓGICA DA APLICAÇÃO ---

def executar_analise_completa(caminho_pdf):
    """Orquestra todo o processo de OCR, extração e consolidação."""
    try:
        with st.spinner("🔍 Etapa 1/3: Lendo e preparando o documento..."):
            texto = aplicar_ocr(caminho_pdf)
            chunks = dividir_em_chunks(texto)
        st.success(f"✅ Documento preparado e dividido em {len(chunks)} partes.")

        progresso_extracaao = st.progress(0, text="Analisando parte 1...")
        with st.spinner(f"🤖 Etapa 2/3: Extraindo dados de cada uma das {len(chunks)} partes..."):
            log_detalhado_chunks = extrair_dados_parciais(chunks, progresso_extracaao)
            st.session_state.log_detalhado = log_detalhado_chunks
            
            resultados_parciais_sucesso = [
                item.get("resultado_recebido")
                for item in log_detalhado_chunks
                if isinstance(item, dict) and item.get("status") == "Sucesso"
            ]

            if not resultados_parciais_sucesso:
                raise ValueError("A extração de dados parciais falhou. Não foi possível encontrar informações nos pedaços do documento.")
        st.success("✅ Extração de dados parciais concluída.")

        with st.spinner("🧠 Etapa 3/3: Consolidando dados e gerando resumo..."):
            dados_completos = consolidar_resultados(resultados_parciais_sucesso)
            if not dados_completos or not isinstance(dados_completos, dict):
                raise ValueError("A etapa de consolidação final falhou. A IA não conseguiu combinar os resultados parciais.")
            
            st.session_state.dados_completos = dados_completos
        st.success("🎉 Análise finalizada com sucesso!")
        st.session_state.estado_app = "finalizado"

    except Exception as e:
        st.session_state.estado_app = "erro"
        st.session_state.error_message = f"Ocorreu um erro durante o processamento: {str(e)}"
        st.session_state.error_details = traceback.format_exc()

def format_key(key):
    """Formata uma chave de dicionário para um título legível."""
    return key.replace('_', ' ').title()

def formatar_parametros(param):
    """Formata o campo de parâmetros para exibição amigável."""
    if not param:
        return "N/A"
    if isinstance(param, str):
        return param
    if isinstance(param, list):
        # Se for uma lista de dicionários ou strings
        return ', '.join([formatar_parametros(p) for p in param])
    if isinstance(param, dict):
        # Formata um dicionário como "chave: valor, chave: valor"
        return ', '.join([f"{format_key(k)}: {v}" for k, v in param.items()])
    return str(param)


def exibir_resultados_formatados():
    """Mostra os resultados finais de forma elegante e profissional."""
    st.header("✅ Análise Concluída", divider="rainbow")
    
    dados = st.session_state.dados_completos
    
    tabs = st.tabs([
        "📝 **Observações Gerais**", "📌 **Dados Processuais**", "👤 **Partes Envolvidas**", 
        "💼 **Contrato de Trabalho**", "📑 **Pleitos e Verbas**", "📊 **Parâmetros de Cálculo**"
    ])
    
    with tabs[0]:
        st.subheader("Resumo Jurídico do Processo")
        resumo = dados.get("observacoes_gerais", "Nenhum resumo jurídico foi gerado.")
        st.markdown(f"<div style='text-align: justify;'>{resumo}</div>", unsafe_allow_html=True)

    with tabs[1]:
        # (código da aba 1 sem alterações)
        st.subheader("Informações Gerais do Processo")
        dados_proc = dados.get("dados_processuais", {})
        if dados_proc and any(dados_proc.values()):
            for key, value in dados_proc.items():
                if value:
                    st.markdown(f"**{format_key(key)}:** {value}")
        else:
            st.info("Nenhum dado processual encontrado.")

    with tabs[2]:
        # (código da aba 2 sem alterações)
        st.subheader("Partes do Processo")
        partes = dados.get("partes", {})
        if partes:
            st.markdown(f"**Reclamante:** {partes.get('reclamante', 'N/A')}")
            st.markdown(f"**CPF:** {partes.get('cpf_reclamante', 'N/A')}")
            st.markdown(f"**Advogado(a) do Reclamante:** {partes.get('advogado_reclamante', 'N/A')}")
            reclamadas = list(filter(None, partes.get("reclamadas", [])))
            if reclamadas:
                st.markdown("**Reclamadas:**")
                for rec in set(reclamadas):
                    st.markdown(f"- {rec}")
        else:
            st.info("Nenhuma parte envolvida encontrada.")

    with tabs[3]:
        # (código da aba 3 sem alterações)
        st.subheader("Detalhes do Contrato de Trabalho")
        contrato = dados.get("contrato_trabalho", {})
        if contrato:
            col1, col2 = st.columns(2)
            with col1:
                st.markdown(f"**Data de Admissão:** {contrato.get('data_admissao') or 'N/A'}")
                st.markdown(f"**Função:** {contrato.get('funcao') or 'N/A'}")
            with col2:
                st.markdown(f"**Data de Demissão:** {contrato.get('data_demissao_rescisao_indireta') or 'N/A'}")
                st.markdown(f"**Salário Base:** {contrato.get('salario_base') or 'N/A'}")
            afastamentos = [af for af in contrato.get("periodos_afastamento", []) if af and af.get("motivo")]
            if afastamentos:
                st.markdown("---")
                st.markdown("**Períodos de Afastamento**")
                df_afast = pd.DataFrame(afastamentos)
                df_afast.rename(columns={'inicio': 'Início', 'fim': 'Fim', 'motivo': 'Motivo'}, inplace=True)
                st.dataframe(df_afast, use_container_width=True, hide_index=True)
        else:
            st.info("Nenhum dado do contrato de trabalho encontrado.")

    with tabs[4]:
        st.subheader("Verbas Reclamadas na Ação")
        verbas_raw = [v for v in dados.get("pleitos_e_verbas", []) if v and v.get("verba")]
        if verbas_raw:
            # --- CORREÇÃO APLICADA AQUI ---
            # Pré-processa a lista de verbas para formatar os parâmetros
            verbas_formatadas = []
            for v in verbas_raw:
                verba_copia = v.copy()
                verba_copia['parametros'] = formatar_parametros(v.get('parametros'))
                verbas_formatadas.append(verba_copia)
            
            df_verbas = pd.DataFrame(verbas_formatadas)
            df_verbas.rename(columns={'verba': 'Verba', 'parametros': 'Parâmetros', 'reflexos': 'Reflexos'}, inplace=True)
            st.dataframe(df_verbas.fillna('N/A'), use_container_width=True, hide_index=True)
        else:
            st.info("Nenhum pleito ou verba encontrado.")

    with tabs[5]:
        # (código da aba 5 sem alterações)
        st.subheader("Parâmetros Definidos para Cálculo")
        params = dados.get("parametros_calculo", {})
        if params:
            honorarios = params.get("honorarios_advocaticios")
            if honorarios and any(honorarios.values()):
                st.markdown("**Honorários Advocatícios**")
                st.markdown(f"- **Percentual:** {honorarios.get('percentual') or 'N/A'}")
                st.markdown(f"- **Base de Cálculo:** {honorarios.get('base_calculo') or 'N/A'}")
            correcao = params.get("correcao_monetaria", [])
            if correcao:
                st.markdown("**Correção Monetária**")
                st.dataframe(pd.DataFrame(correcao), use_container_width=True, hide_index=True)
            juros = params.get("juros_mora", [])
            if juros:
                st.markdown("**Juros de Mora**")
                st.dataframe(pd.DataFrame(juros), use_container_width=True, hide_index=True)
        else:
            st.info("Nenhum parâmetro de cálculo encontrado.")

    st.header("⬇️ Exportar Resultados", divider="rainbow")
    # (código de exportação sem alterações)
    try:
        json_data = json.dumps(dados, indent=2, ensure_ascii=False).encode('utf-8')
        caminho_xml = os.path.join("export", "saida_pjecalc.xml")
        gerar_xml_pjecalc(dados, caminho_xml)
        caminho_docx = os.path.join("export", "resumo_processo.docx")
        gerar_docx_resumo(dados, caminho_docx)

        col1, col2, col3 = st.columns(3)
        with col1:
            st.download_button(label="📥 **Baixar Resumo JSON**", data=json_data, file_name="resumo_final.json", mime="application/json", use_container_width=True)
        with col2:
            with open(caminho_xml, "rb") as f:
                st.download_button(label="📥 **Baixar XML PJe-Calc**", data=f, file_name="saida_pjecalc.xml", mime="application/xml", use_container_width=True)
        with col3:
            with open(caminho_docx, "rb") as f:
                st.download_button(label="📄 **Baixar Resumo Word**", data=f, file_name="resumo_processo.docx", mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document", use_container_width=True)
    except Exception as e:
        st.error(f"Ocorreu um erro ao gerar os arquivos para download: {e}")

    if st.session_state.log_detalhado:
        with st.expander("🐞 Ver Log de Depuração da Extração (para desenvolvedores)"):
            st.json(st.session_state.log_detalhado)

# --- INTERFACE PRINCIPAL ---

def main():
    """Função principal que controla a interface."""
    inicializar_estado()
    
    st.title("📄 PJe-Calc Automático com IA Jurídica")
    st.markdown("Faça o upload de um processo trabalhista em formato PDF para extrair e organizar os dados automaticamente.")

    if st.session_state.estado_app != "inicial":
        if st.button("↻ Analisar Outro Documento", use_container_width=True):
            reiniciar_analise()
            st.rerun()
    
    if st.session_state.estado_app == "finalizado":
        exibir_resultados_formatados()

    elif st.session_state.estado_app == "erro":
        st.error(st.session_state.error_message, icon="🚨")
        if st.session_state.error_details:
            with st.expander("Ver detalhes técnicos do erro"):
                st.code(st.session_state.error_details, language="python")
        if st.session_state.log_detalhado:
            with st.expander("Ver log de depuração da extração"):
                st.json(st.session_state.log_detalhado)

    elif st.session_state.estado_app == "processando":
        caminho_temp_pdf = os.path.join("export", "temp.pdf")
        if os.path.exists(caminho_temp_pdf):
             executar_analise_completa(caminho_temp_pdf)
             st.rerun()
        else:
            st.error("Arquivo PDF não encontrado. Por favor, faça o upload novamente.")
            reiniciar_analise()
            st.rerun()

    elif st.session_state.estado_app == "inicial":
        pdf_file = st.file_uploader(
            label="**Faça o upload do processo trabalhista (formato PDF)**",
            type="pdf",
            help="Arraste o PDF do processo ou clique para selecionar o arquivo."
        )

        if pdf_file:
            os.makedirs("export", exist_ok=True)
            
            caminho_temp_pdf = os.path.join("export", "temp.pdf")
            with open(caminho_temp_pdf, "wb") as f:
                f.write(pdf_file.getbuffer())
            
            st.session_state.estado_app = "processando"
            st.rerun()

if __name__ == "__main__":
    main()
