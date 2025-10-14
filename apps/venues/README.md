# Venues
Zarządza strukturą **obiektów, sal, układów miejsc i sektorów** z miejscami numerowanymi i nienumerowanymi.  
Pozwala odwzorować rzeczywiste układy przestrzenne obiektów – od budynku po pojedyncze miejsce.


## Relacje
Venue -> VenueArea        Obiekt może mieć jedną lub więcej sal/obszarów.
VenueArea -> SeatingPlan  Sala może mieć kilka układów miejsc, np. ustawienie koncertowe, konferencyjne itp.
SeatingPlan -> Section    Układ zawiera sektory z miejscami siedzącymi lub stojącymi.
Section -> Seat           Sektor z miejscami siedzącymi ma numerowane miejsca, ze stojącymi tylko liczbę miejsc.

## Struktura logiczna
```mermaid
mindmap
  root((Obiekt / budynek – Venue))
    Sala / obszar obiektu (VenueArea)
      Układ miejsc / schemat sali (SeatingPlan)
        Sektor (Section)
          Typ sektora
            Miejsca siedzące
              Miejsce (Seat)
                Rząd (row)
                Numer (number)
                Miejsce dla osoby na wózku (is_wheelchair)
            Miejsca stojące
              Liczba miejsc (capacity)

Dlaczego venues?
Aplikacja obsługuje wydarzenia różnych organizatorów w różnych lokalizacjach i obiektach.
Nie wszystkie nstytucje kulturalne posiadają swoje własne obiekty. Są teatry, które nie mają swojej sceny i występując tylko gościnnie.
Z kolei np. w filharmonii, która dysponuje swoją salą, mogą odbywać się imprezy biletowane innych organizatorów.
Czyli adresatem naszej aplikacji od strony biznesu mogą być organizatorzy imprez, agencje sprzedażowe i także właściciele obiektów.

Kategorie i rodzaje biletów
Venues umożliwia jednokrotne wprowadzenie danych dotyczących miejsc w danym obiekcie.
Przy wprowadzaniu wydarzenia można wybrać konkrekty miejsce (np. sala gówna) 
i konkretne ustawienie sali (np. ustawienie koncertowe).
Na poziomie wydarzenia można natomiast skorelować kategorie cenowe biletów z sektorami (np. kat. I, II, VIP)

Pozostałe kwestie od strony zakupu biletu, to
rodzaj biletu: normalny, ulgowy itd.
zniżki: karta lojalnościowa, bon rabatowy itd.

Pod dyskusję.