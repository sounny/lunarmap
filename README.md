# Lunar Arctic (80°N - 90°N) · Real-Time NASA LRO Orbital Atlas

> **Real-Time WebGL2 Planetary Cartography · NASA LRO LOLA, GSFC PGDA & Diviner**  
> **Live Interactive Experience:** [https://sounny.github.io/lunarmap/](https://sounny.github.io/lunarmap/)  
> **Planetary WebGIS Ecosystem:** [JSMARS (https://jsmars.sounny.com)](https://jsmars.sounny.com)

![Lunar Arctic Live Raymarched Interface](screenshots/arctic_sunlight.png)

## Overview

**Lunar Arctic** is a vanilla WebGL2 (zero JavaScript library dependencies) GPU-raymarched planetary atlas of the Moon's North Pole (`80°N to 90°N`, **`IAU_2015:30130`** Moon North Polar Stereographic, `R = 1,737.4 km`) built directly from empirical **NASA Lunar Reconnaissance Orbiter (LRO)** orbital datasets.

Because the lunar equator is inclined by only **1.54°** to the ecliptic (compared to Earth's 23.4°), sunlight at the Lunar North Pole never rises high overhead. At northern summer solstice (`+1.54°` subsolar latitude), the Sun skims horizontally **360° around the horizon**, casting hundred-kilometer crater shadows across cryogenic depressions while bathing narrow crater rims in quasi-continuous sunlight.

Drag the **360° Orbital Sun Ring** (or press **Play**) to raymarch live lunar shadows across a **2048 × 2048** (`296.9 m/px`) 16-bit LOLA elevation grid directly in WebGL2.

---

## Four Orbital Scientific Lenses

| Lens | Physical Phenomenon | Empirical NASA Source & Grid Resolution |
| :--- | :--- | :--- |
| **Sunlight** | Real-time **40-step** 3D spherical horizon raymarching (`+1.54°` northern summer horizon sun) with `0.53°` solar-disc penumbra, near-side-only Earthshine, and Lommel-Seeliger (`μ₀ / (μ₀ + μ)`) lunar reflectance with sRGB gamma transfer. | LRO LOLA `LDEM_80N_80M` (`80 m/px` source, `0.5 m` `int16` step, `~1 m` vertical accuracy; block-averaged to **`296.9 m/px`**, 16-bit RG PNG with `0.13 m` encoding step) |
| **Peak Sunlight** | Highlights narrow polar crests along **Whipple** and **Peary** craters that remain sunlit up to **`89.8%`** (`89.7%` on the native `60 m` grid) of the **18.6-year lunar nodal precession cycle**. | NASA GSFC PGDA Product #69 (2016): `AVGVISIB_85N_060M_201608` (`60 m/px`) & `AVGVISIB_75N_120M_201608` (`120 m/px`), extending Mazarico et al. (2011) |
| **24 K Ice Traps** | Maps **`100,713 km²`** of cryogenic cold-trap terrain (`Tavg ≤ 110 K`) and **`1,631 km²`** of thermally stable surface water frost (`ice_depth = 0.00 m`) across **`14,806 km²`** of Permanently Shadowed Regions (`593.8 m/px` majority-area grid; `16,994 km²` on native `120 m` `LPSR_75N_120M_201608`), reaching a **`24.7 K (-248°C)`** annual mean minimum (`24.4 K` raw facet). | Paige, Sullivan & Williams (2018) UCLA Diviner Level-5 `LRO-L-DLRE-5-PRP-V2.0` + Williams et al. (2019), resampled to **`593.8 m/px`** (`1024 × 1024`) |
| **Outpost Sites** | Live multi-criteria solver for hypothetical northern polar outpost landing ridges, isolating gently sloped (`≤10.0°`), well-lit (`≥60%` solar visibility) terrain within short rover range (`≤5.0 km`) of permanently shadowed regions using true spherical stereographic area. | Coupled `296.9 m/px` LOLA Slope + PGDA Solar Visibility + `593.8 m/px` PSR Proximity |

| Peak Polar Sunlight (`89.8%` Whipple Rim) | 24.7 K Cryogenic Cold Traps |
| :---: | :---: |
| ![Peak Sunlight Mode](screenshots/arctic_eternal_light.png) | ![Cold Traps Mode](screenshots/arctic_cold_traps.png) |

---

## Data Provenance & Integrity

All interface readouts, landmarks, and shaders derive directly from empirical orbital grids (no placeholder HTML numbers, no procedural noise, no synthetic elevation albedo, and official IAU / USGS Gazetteer crater coordinates):

- **Laser Altimetry:** Smith, D. E., et al. (2010). *Initial observations from the Lunar Orbiter Laser Altimeter (LOLA)*. *Geophys. Res. Lett.*, 37, L18204 (`LRO-L-LOLA-4-GDR-V1.0`, `LDEM_80N_80M`).
- **Solar Continuity & PSRs:** NASA GSFC Planetary Geodesy Data Archive (PGDA) **Product #69** (*Lunar Polar Illumination*, 2016: `AVGVISIB_85N_060M_201608`, `AVGVISIB_75N_120M_201608`, `LPSR_75N_120M_201608`), following Mazarico, E., et al. (2011), *Illumination conditions of the lunar polar regions using LOLA topography*, *Icarus*, 211(2), 1066-1081 (`12,866 km²` for contiguous PSRs `> 1 km²` at `240 m/px`).
- **Cryogenic Temperatures & Water-Ice Stability:** Paige, D. A., Sullivan, M. T., & Williams, J.-P. (2018). *LRO DLRE Level 5 Polar Resource Products V2.0* (`LRO-L-DLRE-5-PRP-V2.0`), NASA Planetary Data System (`doi:10.17189/wj0s-w188`); and Williams, J.-P., Greenhagen, B. T., Paige, D. A., et al. (2019), *Seasonal polar temperatures on the Moon*, *J. Geophys. Res.: Planets*, 124(10), 2505-2521 (`doi:10.1029/2019JE006028`).
- **Planetary Nomenclature:** International Astronomical Union (IAU) Working Group for Planetary System Nomenclature / USGS Astrogeology Gazetteer of Planetary Nomenclature (`IAU_2015:30130`).

```bash
# Run locally with any static HTTP server (zero build step)
python -m http.server 8080
```

## Author & License

Created by **Dr. Moulay Anwar Sounny-Slitine** ([sounny.com](https://sounny.com)), Assistant Professor of Earth Observation, GNSS, and GeoAI at the International Space University (ISU).  
Released under the [MIT License](LICENSE).
