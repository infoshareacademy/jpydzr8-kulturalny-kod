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
