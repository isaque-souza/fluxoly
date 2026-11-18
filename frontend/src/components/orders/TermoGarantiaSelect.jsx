import { Select, SelectTrigger, SelectValue, SelectContent, SelectItem } from "@/components/ui/select";

export function textoPrazo(meses) {
  if (!meses) return "sem garantia";
  return meses === 1 ? "1 mês" : `${meses} meses`;
}

// BR-105 -- Termo de Garantia da OS (= Tipo de Garantia: nome + prazo + texto). Um por OS: o prazo vale
// para todos os reparos e o texto sai no PDF de entrega. `termoAtual` mantém visível o termo gravado na
// OS mesmo que tenha sido inativado depois (a lista só traz ativos). `value` é o id em string ("" = nenhum).
export default function TermoGarantiaSelect({ id, value, onChange, termos, termoAtual = null }) {
  const opcoes = termoAtual && !termos.some((t) => t.id === termoAtual.id) ? [termoAtual, ...termos] : termos;
  return (
    <Select value={value} onValueChange={onChange}>
      <SelectTrigger id={id}><SelectValue placeholder="Selecione o Termo de Garantia" /></SelectTrigger>
      <SelectContent>
        {opcoes.map((t) => (
          <SelectItem key={t.id} value={String(t.id)}>
            {t.duracao_meses === undefined ? t.nome : `${t.nome} (${textoPrazo(t.duracao_meses)})`}
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  );
}
