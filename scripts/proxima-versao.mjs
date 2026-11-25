#!/usr/bin/env node
/* global process, console */
// (linha acima: evita erro de ESLint quando o script é copiado para um projeto web)
//
// Calcula a próxima versão semântica a partir dos Conventional Commits
// desde a última tag vX.Y.Z (PGC 3.3 e 9.1).
//
//   feat!: ... ou "BREAKING CHANGE:" no corpo  -> MAJOR
//   feat: ...                                  -> MINOR
//   fix: / perf: ...                           -> PATCH
//   docs, chore, ci, test, refactor, style     -> sem release
//
// Uso:  node scripts/proxima-versao.mjs
//       NOTAS_ARQUIVO=notas.md node scripts/proxima-versao.mjs   (gera também as notas)
// Saída (também gravada em $GITHUB_OUTPUT quando roda no Actions):
//   atual=1.2.0  versao=1.3.0  release=true  tipo=minor

import { execSync } from 'node:child_process';
import { appendFileSync, writeFileSync } from 'node:fs';
import { pathToFileURL } from 'node:url';

export function classificarCommit(mensagem) {
  const [titulo = '', ...corpo] = mensagem.split('\n');
  if (/^\w+(\([^)]*\))?!:/.test(titulo) || /BREAKING CHANGE:/.test(corpo.join('\n'))) {
    return 'major';
  }
  if (/^feat(\([^)]*\))?:/.test(titulo)) return 'minor';
  if (/^(fix|perf)(\([^)]*\))?:/.test(titulo)) return 'patch';
  return 'none';
}

const PESO = { none: 0, patch: 1, minor: 2, major: 3 };

export function tipoDeIncremento(mensagens) {
  return mensagens
    .map(classificarCommit)
    .reduce((maior, atual) => (PESO[atual] > PESO[maior] ? atual : maior), 'none');
}

export function incrementar(versao, tipo) {
  const [major, minor, patch] = versao.split('.').map(Number);
  if (tipo === 'major') return `${major + 1}.0.0`;
  if (tipo === 'minor') return `${major}.${minor + 1}.0`;
  if (tipo === 'patch') return `${major}.${minor}.${patch + 1}`;
  return versao;
}

/** Notas de release agrupadas por tipo de commit (PGC 9.2). */
export function gerarNotas(versao, mensagens) {
  const grupos = { Funcionalidades: [], Correções: [], Outros: [] };
  for (const m of mensagens) {
    const titulo = m.split('\n')[0];
    const tipo = classificarCommit(m);
    if (tipo === 'major' || tipo === 'minor') grupos.Funcionalidades.push(titulo);
    else if (tipo === 'patch') grupos.Correções.push(titulo);
    else grupos.Outros.push(titulo);
  }
  let texto = `## v${versao}\n`;
  for (const [nome, itens] of Object.entries(grupos)) {
    if (itens.length === 0) continue;
    texto += `\n### ${nome}\n${itens.map((i) => `- ${i}`).join('\n')}\n`;
  }
  return texto;
}

function git(cmd) {
  return execSync(`git ${cmd}`, { encoding: 'utf8', stdio: ['ignore', 'pipe', 'ignore'] }).trim();
}

function ultimaTag() {
  try {
    return git('describe --tags --abbrev=0 --match "v[0-9]*.[0-9]*.[0-9]*"');
  } catch {
    return null; // repositório ainda sem tags
  }
}

function main() {
  const tag = ultimaTag();
  const atual = tag ? tag.replace(/^v/, '') : '0.0.0';
  const intervalo = tag ? `${tag}..HEAD` : 'HEAD';
  const SEP = '---fim-do-commit---';
  const log = git(`log ${intervalo} --format=%B${SEP}`);
  const mensagens = log.split(SEP).map((m) => m.trim()).filter(Boolean);

  // Primeira release: se não há tag, começa em 1.0.0.
  let tipo = tipoDeIncremento(mensagens);
  let versao = incrementar(atual, tipo);
  if (!tag && mensagens.length > 0) {
    tipo = 'major';
    versao = '1.0.0';
  }

  if (process.env.NOTAS_ARQUIVO) {
    writeFileSync(process.env.NOTAS_ARQUIVO, gerarNotas(versao, mensagens));
  }

  const saida = { atual, versao, release: String(tipo !== 'none'), tipo };
  for (const [chave, valor] of Object.entries(saida)) {
    console.log(`${chave}=${valor}`);
    if (process.env.GITHUB_OUTPUT) appendFileSync(process.env.GITHUB_OUTPUT, `${chave}=${valor}\n`);
  }
}

if (import.meta.url === pathToFileURL(process.argv[1]).href) {
  main();
}
