# Derivation traces (Nemo --trace)

## offers("d07", "going_out")

```
offers("d07", "going_out")
  ⟵ offers(?D, ?P) :- signalHits(?D, ?P, ?N), required(?P, ?K), ?N >= ?K .
    signalHits("d07", "going_out", 1)
      ⟵ signalHits(?D, ?P, #count(?F)) :- evidence(?D, ?P, ?F, ?L) .
        evidence("d07", "going_out", "nightlife_per_km2", "high")
          ⟵ evidence(?D, ?P, ?F, ?L) :- signal(?P, ?F, ?L), level(?D, ?F, ?L) .
            signal("going_out", "nightlife_per_km2", "high")   [fact]
            level("d07", "nightlife_per_km2", "high")
              ⟵ level(?D, ?F, "high") :- rank(?D, ?F, ?R), ?R >= 15 .
                rank("d07", "nightlife_per_km2", 20)
                  ⟵ rank(?D, ?F, ?N) :- below(?D, ?F, ?N) .
                    below("d07", "nightlife_per_km2", 20)
                      ⟵ below(?D, ?F, #count(?E)) :- feature(?D, ?F, ?X), feature(?E, ?F, ?Y), ?Y < ?X .
                        feature("d07", "nightlife_per_km2", 41.61)
                          ⟵ feature(?D, "nightlife_per_km2", ?X) :- venues(?D, "nightlife_venue", ?N), areaKm2(?D, ?A), ?X = ?N / ?A .
                            venues("d07", "nightlife_venue", 67)
                              ⟵ venues(?D, ?Class, ?N) :- classCount(?D, ?Class, ?N) .
                                classCount("d07", "nightlife_venue", 67)
                                  ⟵ classCount(?D, ?Class, #count(?P)) :- isA(?P, ?Class), located(?P, ?D), countedClass(?Class) .
                                    isA("osm:node/256669972", "nightlife_venue")
                                      ⟵ isA(?P, ?Super) :- isA(?P, ?Class), subClassOfT(?Class, ?Super) .
                                        isA("osm:node/256669972", "pub")
                                          ⟵ isA(?P, ?Category) :- poiSrc(?P, ?Category, ?D, ?Source) .
                                            poiSrc("osm:node/256669972", "pub", "d07", "osm")   [fact]
                                        subClassOfT("pub", "nightlife_venue")
                                          ⟵ subClassOfT(?A, ?B) :- subClassOf(?A, ?B) .
                                            subClassOf("pub", "nightlife_venue")   [fact]
                                    located("osm:node/256669972", "d07")
                                      ⟵ located(?P, ?D) :- poiSrc(?P, ?Category, ?D, ?Source) .
                                        poiSrc("osm:node/256669972", "pub", "d07", "osm")   [fact]
                                    countedClass("nightlife_venue")   [fact]
                            areaKm2("d07", 1.61)
                              ⟵ areaKm2(?D, ?A) :- value(?D, "area_km2", ?A) .
                                value("d07", "area_km2", 1.61)   [fact]
                        feature("d02", "nightlife_per_km2", 2.963)
                          ⟵ feature(?D, "nightlife_per_km2", ?X) :- venues(?D, "nightlife_venue", ?N), areaKm2(?D, ?A), ?X = ?N / ?A .
                            venues("d02", "nightlife_venue", 57)
                              ⟵ venues(?D, ?Class, ?N) :- classCount(?D, ?Class, ?N) .
                                classCount("d02", "nightlife_venue", 57)
                                  ⟵ classCount(?D, ?Class, #count(?P)) :- isA(?P, ?Class), located(?P, ?D), countedClass(?Class) .
                                    isA("osm:node/267275362", "nightlife_venue")
                                      ⟵ isA(?P, ?Super) :- isA(?P, ?Class), subClassOfT(?Class, ?Super) .
                                        isA("osm:node/267275362", "pub")
                                          ⟵ isA(?P, ?Category) :- poiSrc(?P, ?Category, ?D, ?Source) .
                                            poiSrc("osm:node/267275362", "pub", "d02", "osm")   [fact]
                                        subClassOfT("pub", "nightlife_venue")
                                          ⟵ subClassOfT(?A, ?B) :- subClassOf(?A, ?B) .
                                            subClassOf("pub", "nightlife_venue")   [fact]
                                    located("osm:node/267275362", "d02")
                                      ⟵ located(?P, ?D) :- poiSrc(?P, ?Category, ?D, ?Source) .
                                        poiSrc("osm:node/267275362", "pub", "d02", "osm")   [fact]
                                    countedClass("nightlife_venue")   [fact]
                            areaKm2("d02", 19.24)
                              ⟵ areaKm2(?D, ?A) :- value(?D, "area_km2", ?A) .
                                value("d02", "area_km2", 19.24)   [fact]
    required("going_out", 1)   [fact]
```

## offers("d02", "green_quiet")

```
offers("d02", "green_quiet")
  ⟵ offers(?D, ?P) :- signalHits(?D, ?P, ?N), required(?P, ?K), ?N >= ?K .
    signalHits("d02", "green_quiet", 2)
      ⟵ signalHits(?D, ?P, #count(?F)) :- evidence(?D, ?P, ?F, ?L) .
        evidence("d02", "green_quiet", "park_share", "high")
          ⟵ evidence(?D, ?P, ?F, ?L) :- signal(?P, ?F, ?L), level(?D, ?F, ?L) .
            signal("green_quiet", "park_share", "high")   [fact]
            level("d02", "park_share", "high")
              ⟵ level(?D, ?F, "high") :- rank(?D, ?F, ?R), ?R >= 15 .
                rank("d02", "park_share", 22)
                  ⟵ rank(?D, ?F, ?N) :- below(?D, ?F, ?N) .
                    below("d02", "park_share", 22)
                      ⟵ below(?D, ?F, #count(?E)) :- feature(?D, ?F, ?X), feature(?E, ?F, ?Y), ?Y < ?X .
                        feature("d02", "park_share", 0.1841)
                          ⟵ feature(?D, "park_share", ?X) :- parkArea(?D, ?P), areaKm2(?D, ?A), ?X = ?P / ?A * 1e+06 .
                            parkArea("d02", 3.543e+06)
                              ⟵ parkArea(?D, #sum(?A,?P)) :- isA(?P, "park"), located(?P, ?D), area(?P, ?A) .
                                isA("wfs:PARKINFOOGD.3855709", "park")
                                  ⟵ isA(?P, ?Category) :- poiSrc(?P, ?Category, ?D, ?Source) .
                                    poiSrc("wfs:PARKINFOOGD.3855709", "park", "d02", "parks")   [fact]
                                located("wfs:PARKINFOOGD.3855709", "d02")
                                  ⟵ located(?P, ?D) :- poiSrc(?P, ?Category, ?D, ?Source) .
                                    poiSrc("wfs:PARKINFOOGD.3855709", "park", "d02", "parks")   [fact]
                                area("wfs:PARKINFOOGD.3855709", 603)   [fact]
                            areaKm2("d02", 19.24)
                              ⟵ areaKm2(?D, ?A) :- value(?D, "area_km2", ?A) .
                                value("d02", "area_km2", 19.24)   [fact]
                        feature("d01", "park_share", 0.0533)
                          ⟵ feature(?D, "park_share", ?X) :- parkArea(?D, ?P), areaKm2(?D, ?A), ?X = ?P / ?A * 1e+06 .
                            parkArea("d01", 1.53e+05)
                              ⟵ parkArea(?D, #sum(?A,?P)) :- isA(?P, "park"), located(?P, ?D), area(?P, ?A) .
                                isA("wfs:PARKINFOOGD.3855748", "park")
                                  ⟵ isA(?P, ?Category) :- poiSrc(?P, ?Category, ?D, ?Source) .
                                    poiSrc("wfs:PARKINFOOGD.3855748", "park", "d01", "parks")   [fact]
                                located("wfs:PARKINFOOGD.3855748", "d01")
                                  ⟵ located(?P, ?D) :- poiSrc(?P, ?Category, ?D, ?Source) .
                                    poiSrc("wfs:PARKINFOOGD.3855748", "park", "d01", "parks")   [fact]
                                area("wfs:PARKINFOOGD.3855748", 945)   [fact]
                            areaKm2("d01", 2.87)
                              ⟵ areaKm2(?D, ?A) :- value(?D, "area_km2", ?A) .
                                value("d01", "area_km2", 2.87)   [fact]
    required("green_quiet", 2)   [fact]
```

## ride("at:49:633", "at:49:657", "U1", 15)

```
ride("at:49:633" (Kagraner Platz), "at:49:657" (Karlsplatz), "U1", 15)
  ⟵ ride(?H, ?Next, ?Line, ?T) :- ride(?H, ?S, ?Line, ?T1), segment(?S, ?Next, ?Line, ?T2, ?Trips), ?T = ?T1 + ?T2, ?T <= 45 .
    ride("at:49:633" (Kagraner Platz), "at:49:1320" (Stephansplatz), "U1", 13)
      ⟵ ride(?H, ?Next, ?Line, ?T) :- ride(?H, ?S, ?Line, ?T1), segment(?S, ?Next, ?Line, ?T2, ?Trips), ?T = ?T1 + ?T2, ?T <= 45 .
        ride("at:49:633" (Kagraner Platz), "at:49:1198" (Schwedenplatz), "U1", 12)
          ⟵ ride(?H, ?Next, ?Line, ?T) :- ride(?H, ?S, ?Line, ?T1), segment(?S, ?Next, ?Line, ?T2, ?Trips), ?T = ?T1 + ?T2, ?T <= 45 .
            ride("at:49:633" (Kagraner Platz), "at:49:916" (Nestroyplatz), "U1", 11)
              ⟵ ride(?H, ?Next, ?Line, ?T) :- ride(?H, ?S, ?Line, ?T1), segment(?S, ?Next, ?Line, ?T2, ?Trips), ?T = ?T1 + ?T2, ?T <= 45 .
                ride("at:49:633" (Kagraner Platz), "at:49:1040" (Praterstern), "U1", 9)
                  ⟵ ride(?H, ?Next, ?Line, ?T) :- ride(?H, ?S, ?Line, ?T1), segment(?S, ?Next, ?Line, ?T2, ?Trips), ?T = ?T1 + ?T2, ?T <= 45 .
                    ride("at:49:633" (Kagraner Platz), "at:49:1433" (Vorgartenstraße), "U1", 8)
                      ⟵ ride(?H, ?Next, ?Line, ?T) :- ride(?H, ?S, ?Line, ?T1), segment(?S, ?Next, ?Line, ?T2, ?Trips), ?T = ?T1 + ?T2, ?T <= 45 .
                        ride("at:49:633" (Kagraner Platz), "at:49:234" (Donauinsel), "U1", 6)
                          ⟵ ride(?H, ?Next, ?Line, ?T) :- ride(?H, ?S, ?Line, ?T1), segment(?S, ?Next, ?Line, ?T2, ?Trips), ?T = ?T1 + ?T2, ?T <= 45 .
                            ride("at:49:633" (Kagraner Platz), "at:49:641" (Kaisermühlen-VIC), "U1", 5)
                              ⟵ ride(?H, ?Next, ?Line, ?T) :- ride(?H, ?S, ?Line, ?T1), segment(?S, ?Next, ?Line, ?T2, ?Trips), ?T = ?T1 + ?T2, ?T <= 45 .
                                ride("at:49:633" (Kagraner Platz), "at:49:31" (Alte Donau), "U1", 4)
                                  ⟵ ride(?H, ?Next, ?Line, ?T) :- ride(?H, ?S, ?Line, ?T1), segment(?S, ?Next, ?Line, ?T2, ?Trips), ?T = ?T1 + ?T2, ?T <= 45 .
                                    ride("at:49:633" (Kagraner Platz), "at:49:627" (Kagran), "U1", 2)
                                      ⟵ ride(?H, ?S, ?Line, ?T) :- hub(?D, ?H), segment(?H, ?S, ?Line, ?T, ?Trips) .
                                        hub("d22", "at:49:633" (Kagraner Platz))
                                          ⟵ hub(?D, ?S) :- stationIn(?S, ?D), departures(?S, ?X), busiest(?D, ?X) .
                                            stationIn("at:49:633" (Kagraner Platz), "d22")   [fact]
                                            departures("at:49:633" (Kagraner Platz), 22326)
                                              ⟵ departures(?S, #sum(?Trips,?Next, ?Line)) :- segment(?S, ?Next, ?Line, ?Minutes, ?Trips) .
                                                segment("at:49:633" (Kagraner Platz), "at:49:716" (Kraygasse), "N24", 3, 48)   [fact]
                                            busiest("d22", 22326)
                                              ⟵ busiest(?D, #max(?X)) :- stationIn(?S, ?D), departures(?S, ?X) .
                                                stationIn("at:49:1619" (Kalmusweg), "d22")   [fact]
                                                departures("at:49:1619" (Kalmusweg), 4)
                                                  ⟵ departures(?S, #sum(?Trips,?Next, ?Line)) :- segment(?S, ?Next, ?Line, ?Minutes, ?Trips) .
                                                    segment("at:49:1619" (Kalmusweg), "at:49:1279" (Breitenlee, Spargelfeldstraße), "85A", 1, 4)   [fact]
                                        segment("at:49:633" (Kagraner Platz), "at:49:627" (Kagran), "U1", 2, 4944)   [fact]
                                    segment("at:49:627" (Kagran), "at:49:31" (Alte Donau), "U1", 2, 4944)   [fact]
                                segment("at:49:31" (Alte Donau), "at:49:641" (Kaisermühlen-VIC), "U1", 1, 4944)   [fact]
                            segment("at:49:641" (Kaisermühlen-VIC), "at:49:234" (Donauinsel), "U1", 1, 4944)   [fact]
                        segment("at:49:234" (Donauinsel), "at:49:1433" (Vorgartenstraße), "U1", 2, 4944)   [fact]
                    segment("at:49:1433" (Vorgartenstraße), "at:49:1040" (Praterstern), "U1", 1, 4944)   [fact]
                segment("at:49:1040" (Praterstern), "at:49:916" (Nestroyplatz), "U1", 2, 4944)   [fact]
            segment("at:49:916" (Nestroyplatz), "at:49:1198" (Schwedenplatz), "U1", 1, 4944)   [fact]
        segment("at:49:1198" (Schwedenplatz), "at:49:1320" (Stephansplatz), "U1", 1, 4944)   [fact]
    segment("at:49:1320" (Stephansplatz), "at:49:657" (Karlsplatz), "U1", 2, 4946)   [fact]
```
