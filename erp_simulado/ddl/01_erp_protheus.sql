-- ERP Protheus simulado: tabelas SC5, SC6, SA1, SA3 e SB1 por empresa (sufixo <empresa>0),
-- com os campos de controle do Protheus (D_E_L_E_T_, R_E_C_N_O_ e S_T_A_M_P_).
-- Executado automaticamente pelo container do PostgreSQL na primeira inicialização.

CREATE OR REPLACE FUNCTION public.fn_atualiza_stamp() RETURNS trigger
LANGUAGE plpgsql AS $$
BEGIN
    -- Como no Protheus, o S_T_A_M_P_ registra o momento (UTC) de toda inclusão ou alteração.
    NEW.s_t_a_m_p_ := timezone('UTC', clock_timestamp());
    RETURN NEW;
END;
$$;

DO $$
DECLARE
    emp text;
    tab text;
BEGIN
    FOREACH emp IN ARRAY ARRAY['01', '05', '08', '13'] LOOP
        EXECUTE format($ddl$
            CREATE TABLE IF NOT EXISTS %I (
                c5_filial    char(2)  NOT NULL,
                c5_num       char(6)  NOT NULL,
                c5_tipo      char(1)  NOT NULL DEFAULT 'N',
                c5_cliente   char(6)  NOT NULL,
                c5_lojacli   char(2)  NOT NULL,
                c5_vend1     char(6)  NOT NULL DEFAULT ' ',
                c5_emissao   char(8)  NOT NULL,
                c5_nota      char(9)  NOT NULL DEFAULT ' ',
                d_e_l_e_t_   char(1)  NOT NULL DEFAULT ' ',
                r_e_c_n_o_   bigserial PRIMARY KEY,
                s_t_a_m_p_   timestamp
            )$ddl$, 'sc5' || emp || '0');

        EXECUTE format($ddl$
            CREATE TABLE IF NOT EXISTS %I (
                c6_filial    char(2)       NOT NULL,
                c6_num       char(6)       NOT NULL,
                c6_item      char(2)       NOT NULL,
                c6_produto   char(15)      NOT NULL,
                c6_qtdven    numeric(12,2) NOT NULL,
                c6_prcven    numeric(14,2) NOT NULL,
                c6_valor     numeric(14,2) NOT NULL,
                c6_qtdent    numeric(12,2) NOT NULL DEFAULT 0,
                c6_nota      char(9)       NOT NULL DEFAULT ' ',
                d_e_l_e_t_   char(1)       NOT NULL DEFAULT ' ',
                r_e_c_n_o_   bigserial PRIMARY KEY,
                s_t_a_m_p_   timestamp
            )$ddl$, 'sc6' || emp || '0');

        EXECUTE format($ddl$
            CREATE TABLE IF NOT EXISTS %I (
                a1_filial    char(2)     NOT NULL DEFAULT ' ',
                a1_cod       char(6)     NOT NULL,
                a1_loja      char(2)     NOT NULL,
                a1_nome      varchar(40) NOT NULL,
                a1_nreduz    varchar(20) NOT NULL,
                a1_est       char(2)     NOT NULL,
                a1_mun       varchar(60) NOT NULL,
                a1_cgc       char(14)    NOT NULL,
                a1_vend      char(6)     NOT NULL DEFAULT ' ',
                a1_msblql    char(1)     NOT NULL DEFAULT '2',
                d_e_l_e_t_   char(1)     NOT NULL DEFAULT ' ',
                r_e_c_n_o_   bigserial PRIMARY KEY,
                s_t_a_m_p_   timestamp
            )$ddl$, 'sa1' || emp || '0');

        EXECUTE format($ddl$
            CREATE TABLE IF NOT EXISTS %I (
                a3_filial    char(2)     NOT NULL DEFAULT ' ',
                a3_cod       char(6)     NOT NULL,
                a3_nome      varchar(40) NOT NULL,
                d_e_l_e_t_   char(1)     NOT NULL DEFAULT ' ',
                r_e_c_n_o_   bigserial PRIMARY KEY,
                s_t_a_m_p_   timestamp
            )$ddl$, 'sa3' || emp || '0');

        EXECUTE format($ddl$
            CREATE TABLE IF NOT EXISTS %I (
                b1_filial    char(2)       NOT NULL DEFAULT ' ',
                b1_cod       char(15)      NOT NULL,
                b1_desc      varchar(30)   NOT NULL,
                b1_tipo      char(2)       NOT NULL DEFAULT 'PA',
                b1_um        char(2)       NOT NULL,
                b1_grupo     char(4)       NOT NULL,
                b1_prv1      numeric(14,2) NOT NULL,
                d_e_l_e_t_   char(1)       NOT NULL DEFAULT ' ',
                r_e_c_n_o_   bigserial PRIMARY KEY,
                s_t_a_m_p_   timestamp
            )$ddl$, 'sb1' || emp || '0');

        FOREACH tab IN ARRAY ARRAY['sc5', 'sc6', 'sa1', 'sa3', 'sb1'] LOOP
            EXECUTE format('DROP TRIGGER IF EXISTS trg_stamp ON %I', tab || emp || '0');
            EXECUTE format(
                'CREATE TRIGGER trg_stamp BEFORE INSERT OR UPDATE ON %I '
                'FOR EACH ROW EXECUTE FUNCTION public.fn_atualiza_stamp()', tab || emp || '0');
            EXECUTE format('CREATE INDEX IF NOT EXISTS %I ON %I (s_t_a_m_p_)',
                           'ix_' || tab || emp || '0_stamp', tab || emp || '0');
        END LOOP;
    END LOOP;
END;
$$;
