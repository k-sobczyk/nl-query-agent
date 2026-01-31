# holisticon-recrutiment


# Workflow
1) Przerzucenie wartości z jsona do bazy SQL.
2) LLM + Function Calling + Pydantic
3) Feedback Loop do modelu jeśli użytkownik zapytałby o coś innego lub podałby złe parametry.

# Pydantic


# Backend
1. Query Builder po walidacji z modelu Pydantica -> tutaj używać (np. %s w psycopg2 lub :value w SQLAlchemy), a nie podawać wartości w stringu.

2. Co jeśli baza nic nie zwróci? Co jeśli baza zwróci 10 milionów rekordów? (hardcoded LIMIT)
- Limitowanie (Guardrails)
- Obsługa braku danych - brak wyników dla podanych filtrów. LLM wtedy grzecznie odpowie użytkownikowi, zamiast zmyślać (halucynować) dane.


3. Natomiast jeśli te dane są to ja nie chce ich wrzucać do LLM'a, dane nie powinny do niego trafiać ale informacja o tym jak przebiegło query, ile trawało ile rekordów zwróciło juz moze

natomiast same dane z bazy mają nie trafiać do LLM'a


4. Model musi znać aktualną datę



Produkcja
- Rate Limited
- Circuit Breaker
- Kolejka (?)
- Logowanie danych i zapis użytkowania aplikacji
- Cacheowanie (Redis)
