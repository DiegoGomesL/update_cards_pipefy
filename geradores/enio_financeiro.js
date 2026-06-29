const { Client } = require('pg');
const fs = require('fs');
const path = require('path');

const casos = JSON.parse(fs.readFileSync(path.join(__dirname,'..','..','relatorios','dados','enio_casos.json'),'utf-8'));
const norm = c => String(c||'').replace(/\D/g,'');

const allCpfs   = [...new Set(casos.map(c=>norm(c.cpf_limpo||c.cpf)).filter(Boolean))];
const defAdm    = [...new Set(casos.filter(c=>(c.resultado_adm||'').toUpperCase()==='DEFERIDO').map(c=>norm(c.cpf_limpo||c.cpf)))];
const procJud   = [...new Set(casos.filter(c=>/PROCEDENTE/.test((c.resultado_jud||'').toUpperCase()) && !/IMPROCEDENTE/.test((c.resultado_jud||'').toUpperCase())).map(c=>norm(c.cpf_limpo||c.cpf)))];

const client = new Client({host:'localhost',port:5433,database:'teles_db',user:'teles_admin',password:'telesecostaPedro@2021',ssl:false});

const RECEB = "f.status IN ('Pago no prazo','Pago com atraso','Recebido sem data prevista')";

async function grupo(cpfs, label){
  const q = `
    SELECT
      COUNT(DISTINCT f.cpf_limpo)                                   AS cpfs,
      COUNT(*)                                                      AS parcelas,
      SUM(f.valor_numerico)                                         AS total,
      SUM(f.valor_numerico) FILTER (WHERE ${RECEB})                AS recebido,
      SUM(f.valor_numerico) FILTER (WHERE f.status='Atrasado')     AS em_atraso,
      SUM(f.valor_numerico) FILTER (WHERE f.status='No prazo')     AS no_prazo,
      SUM(f.valor_numerico) FILTER (WHERE f.status='Sem informação') AS sem_info
    FROM pipefy.vw_financeiro_temporal_clean f
    WHERE f.cpf_limpo = ANY($1)`;
  const r = await client.query(q,[cpfs]);
  return {label, n_cpfs_lista:cpfs.length, ...r.rows[0]};
}

client.connect().then(async()=>{
  const tot = await grupo(allCpfs,'TODOS ENIO');
  const da  = await grupo(defAdm,'DEFERIDO ADM');
  const pj  = await grupo(procJud,'PROCEDENTE JUD');
  // ganhos (won = defAdm ∪ procJud)
  const won = [...new Set([...defAdm,...procJud])];
  const wg  = await grupo(won,'GANHOS (lastro)');

  const out = {todos:tot, deferido_adm:da, procedente_jud:pj, ganhos:wg,
    contrato:{valor_contrato:412500.00, investimento_fundo:150000.00, qtd_processos_contratados:129}};
  fs.writeFileSync(path.join(__dirname,'..','..','relatorios','dados','enio_financeiro.json'), JSON.stringify(out,null,2),'utf-8');

  const f = x => x==null?'—':('R$ '+Number(x).toLocaleString('pt-BR',{minimumFractionDigits:2,maximumFractionDigits:2}));
  for(const g of [tot,da,pj,wg]){
    console.log(`\n=== ${g.label} (${g.cpfs} c/ financeiro de ${g.n_cpfs_lista} na lista) ===`);
    console.log('  total       :', f(g.total));
    console.log('  recebido    :', f(g.recebido));
    console.log('  em atraso   :', f(g.em_atraso));
    console.log('  no prazo    :', f(g.no_prazo));
    console.log('  sem info    :', f(g.sem_info));
    const aReceber = Number(g.em_atraso||0)+Number(g.no_prazo||0)+Number(g.sem_info||0);
    console.log('  a receber   :', f(aReceber));
    if(g.cpfs>0 && (g.label.includes('DEFERIDO')||g.label.includes('PROCEDENTE')))
      console.log('  valor/proc  :', f(Number(g.total)/g.cpfs));
  }
  console.log('\nSalvo: enio_financeiro.json');
  await client.end();
}).catch(e=>{console.error('ERR:',e.message);process.exit(1);});
