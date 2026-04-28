# Teste ultra-simples: apenas ver se a tabela existe
res = supabase.from_("pessoas").select("*").limit(1).execute()
