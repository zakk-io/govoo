# CLAGOV bundled font sources

Retrieved on 2026-10-22 from the official Google Fonts repository.
Repository: https://github.com/google/fonts
Pinned revision: `45e3d5269e4a17d823f6d84470bc084dc5ae46f6`.

## Distributed assets

| CSS family | Weight | Style | TrueType file | Web file |
| --- | ---: | --- | --- | --- |
| Inter | 400 | normal | Inter-Regular.ttf | Inter-Regular.woff2 |
| Inter | 500 | normal | Inter-Medium.ttf | Inter-Medium.woff2 |
| Inter | 600 | normal | Inter-SemiBold.ttf | Inter-SemiBold.woff2 |
| Inter | 700 | normal | Inter-Bold.ttf | Inter-Bold.woff2 |
| CLAGOV Display | 600 | normal | CLAGOVDisplay-SemiBold.ttf | CLAGOVDisplay-SemiBold.woff2 |

All fonts contain their full upstream character coverage; no subset was applied.
The TTF versions use static TrueType outlines for compatibility with report renderers.
The WOFF2 versions contain the same glyphs, outlines, character maps, and advance widths.

## Original sources and licenses

The two OFL text files are byte-for-byte copies of the upstream licenses, including original copyright notices.
The fonts, including these derived versions, remain licensed under the SIL Open Font License 1.1; the add-on's code license does not replace it.

### inter

- Source: [Inter[opsz,wght].ttf](https://raw.githubusercontent.com/google/fonts/45e3d5269e4a17d823f6d84470bc084dc5ae46f6/ofl/inter/Inter%5Bopsz%2Cwght%5D.ttf)
  SHA-256: `29160a80ff49ddcab2c97711247e08b1fab27a484a329ce8b813d820dc559031`
- Source: [OFL.txt](https://raw.githubusercontent.com/google/fonts/45e3d5269e4a17d823f6d84470bc084dc5ae46f6/ofl/inter/OFL.txt)
  SHA-256: `5b9321a4298cfeb6b34354164a1c3afc3db114569984c502b9b35d988fd58c57`

### playfairdisplay

- Source: [PlayfairDisplay[wght].ttf](https://raw.githubusercontent.com/google/fonts/45e3d5269e4a17d823f6d84470bc084dc5ae46f6/ofl/playfairdisplay/PlayfairDisplay%5Bwght%5D.ttf)
  SHA-256: `c40f2293766a503bc70cce9e512ef844a4ccb7cbcde792fe2ea31d191917d8d6`
- Source: [OFL.txt](https://raw.githubusercontent.com/google/fonts/45e3d5269e4a17d823f6d84470bc084dc5ae46f6/ofl/playfairdisplay/OFL.txt)
  SHA-256: `566be814f8e96e93dfa16101331557eb6b5467e9e03f627c0910fe93ca12300e`

## Modifications and family naming

Generated with fontTools 4.60.1 and Brotli 1.1.0.
Variable fonts were fully instantiated with fontTools.varLib.instancer.instantiateVariableFont, updateFontNames=True.
Inter uses opsz=14 and wght=400/500/600/700. Its license declares no Reserved Font Name, so the Inter family name is retained.
Playfair Display uses wght=600. Its license reserves the name Playfair Display, so the derived font's primary family and PostScript identity were renamed to CLAGOV Display and ClagovDisplay-SemiBold. Original authorship and copyright metadata remain intact.
Use CSS family `Inter` for the four Inter weights and `CLAGOV Display` for the display weight. Declare each font-face with font-style: normal and its listed font-weight.
No italics or synthesized additional weights are supplied.

## Verification

Every output was reopened and all tables decoded with fontTools checksum checks enabled. All files have static TrueType glyf/loca tables, no fvar/gvar tables, the expected OS/2 weight, non-italic flags, and fsType=0 embedding permissions.
TTF and WOFF2 character maps, glyph order, advance widths, and every glyph's outline commands were compared for equality. Basic Latin, accented e, and euro codepoints were checked. Renamed primary identity records were checked for absence of the reserved source name.
SHA256SUMS covers every distributed font, license, and this provenance file; verify from this directory with sha256sum --check SHA256SUMS.
