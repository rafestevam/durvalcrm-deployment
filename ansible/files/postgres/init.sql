-- =================================================================
-- SCRIPT DE CRIAÇÃO DO SCHEMA PARA O BANCO 'durvalcrm_dev'
-- Baseado nas entidades JPA do projeto
-- =================================================================

-- Tabela principal para os associados (AssociadoEntity.java)
CREATE TABLE IF NOT EXISTS associados (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    nome_completo VARCHAR(255) NOT NULL,
    cpf VARCHAR(14) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    telefone VARCHAR(20),
    ativo BOOLEAN NOT NULL DEFAULT TRUE,
    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabela para controlar as mensalidades (MensalidadeEntity.java)
CREATE TABLE IF NOT EXISTS mensalidades (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    associado_id UUID NOT NULL REFERENCES associados(id),
    mes_referencia INTEGER NOT NULL CHECK (mes_referencia >= 1 AND mes_referencia <= 12),
    ano_referencia INTEGER NOT NULL CHECK (ano_referencia >= 2020 AND ano_referencia <= 2030),
    valor NUMERIC(10, 2) NOT NULL CHECK (valor > 0),
    status VARCHAR(20) NOT NULL DEFAULT 'PENDENTE',
    data_vencimento DATE NOT NULL,
    data_pagamento TIMESTAMP,
    metodo_pagamento VARCHAR(50),
    qr_code_pix VARCHAR(1000),
    identificador_pix VARCHAR(50) NOT NULL UNIQUE,
    criado_em TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(associado_id, mes_referencia, ano_referencia)
);

-- Tabela para vendas (VendaEntity.java)
CREATE TABLE IF NOT EXISTS vendas (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    descricao VARCHAR(255) NOT NULL,
    valor NUMERIC(10, 2) NOT NULL,
    origem VARCHAR(50) NOT NULL,
    forma_pagamento VARCHAR(50) NOT NULL,
    data_venda TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    criado_em TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    atualizado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabela para doações (DoacaoEntity.java)
CREATE TABLE IF NOT EXISTS doacoes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    associado_id UUID REFERENCES associados(id) ON DELETE SET NULL,
    valor NUMERIC(10, 2) NOT NULL CHECK (valor >= 0),
    tipo VARCHAR(20) NOT NULL,
    status VARCHAR(20) NOT NULL,
    descricao VARCHAR(500),
    data_doacao TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    data_confirmacao TIMESTAMP,
    codigo_transacao VARCHAR(255),
    metodo_pagamento VARCHAR(50),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Índices para performance - associados
CREATE INDEX IF NOT EXISTS idx_associados_cpf ON associados(cpf);
CREATE INDEX IF NOT EXISTS idx_associados_email ON associados(email);
CREATE INDEX IF NOT EXISTS idx_associados_ativo ON associados(ativo);

-- Índices para performance - mensalidades
CREATE INDEX IF NOT EXISTS idx_mensalidades_associado_id ON mensalidades(associado_id);
CREATE INDEX IF NOT EXISTS idx_mensalidades_periodo ON mensalidades(ano_referencia, mes_referencia);
CREATE INDEX IF NOT EXISTS idx_mensalidades_status ON mensalidades(status);
CREATE INDEX IF NOT EXISTS idx_mensalidades_vencimento ON mensalidades(data_vencimento);
CREATE INDEX IF NOT EXISTS idx_mensalidades_identificador_pix ON mensalidades(identificador_pix);

-- Índices para performance - vendas
CREATE INDEX IF NOT EXISTS idx_vendas_origem ON vendas(origem);
CREATE INDEX IF NOT EXISTS idx_vendas_forma_pagamento ON vendas(forma_pagamento);
CREATE INDEX IF NOT EXISTS idx_vendas_data_venda ON vendas(data_venda);

-- Índices para performance - doacoes
CREATE INDEX IF NOT EXISTS idx_doacoes_associado_id ON doacoes(associado_id);
CREATE INDEX IF NOT EXISTS idx_doacoes_status ON doacoes(status);
CREATE INDEX IF NOT EXISTS idx_doacoes_tipo ON doacoes(tipo);
CREATE INDEX IF NOT EXISTS idx_doacoes_data_doacao ON doacoes(data_doacao);
CREATE INDEX IF NOT EXISTS idx_doacoes_data_confirmacao ON doacoes(data_confirmacao);

-- Nota: Triggers e funções comentadas devido a limitações do parser
-- Elas podem ser executadas manualmente se necessário

-- Trigger function para atualizar updated_at automaticamente
-- CREATE OR REPLACE FUNCTION update_updated_at_column()
-- RETURNS TRIGGER AS $$
-- BEGIN
--     NEW.updated_at = CURRENT_TIMESTAMP;
--     RETURN NEW;
-- END;
-- $$ LANGUAGE plpgsql;

-- Trigger para vendas
-- CREATE TRIGGER update_vendas_updated_at 
--     BEFORE UPDATE ON vendas 
--     FOR EACH ROW 
--     EXECUTE FUNCTION update_updated_at_column();

-- Trigger para doacoes
-- CREATE TRIGGER update_doacoes_updated_at 
--     BEFORE UPDATE ON doacoes 
--     FOR EACH ROW 
--     EXECUTE FUNCTION update_updated_at_column();

-- Grant permissions para o usuário da aplicação (comentado devido ao parser)
-- GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO durvalcrm_user;
-- GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO durvalcrm_user;
-- GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO durvalcrm_user;