test_txt = '''
Please process following caption so that:
each subfigure caption is in one line and separated by a newline character;
each subfigure caption should contain a scientific name enclosed in underlined brackets;
each subfigure caption should contains specimen information if available;
each subfigure caption should contain a scale bar information if available.

For example:
Figure 3.
Pojetaia runnegari Jell, 1980 from the Shackleton Limestone. (1–4)
Specimen SMNH Mo185039 in (1) lateral view, (2) dorsal view, (3) magniﬁca-
tion of the central margin, showing laminar crystalline imprints, (4) magniﬁca-
tion of the cardinal teeth shown in (2). (5, 6) Specimen SMNH Mo185040,
(5) lateral view, (6) magniﬁcation of lateral surface, showing laminar crystalline
imprints. (7) Specimen SMNH Mo185041 in lateral view. (8) Specimen SMNH
Mo185042 in lateral view. (9) Specimen SMNH Mo185043. (5, 6, 8) imaged
under low vacuum settings. (1, 2, 6–9) Scale bars = 200 µm; (3–5) scale bars
= 100 µm.

Paragraph above should be converted to:
1. _Pojetaia runnegari_ SMNH Mo185039, lateral view (200 µm scale bar).
2. _Pojetaia runnegari_ SMNH Mo185039, dorsal view (200 µm scale bar).
3. _Pojetaia runnegari_ SMNH Mo185039, magnification of central margin, showing laminar crystalline imprints (100 µm scale bar).
4. _Pojetaia runnegari_ SMNH Mo185039, magnification of cardinal teeth (100 µm scale bar).
5. _Pojetaia runnegari_ SMNH Mo185040, lateral view (100 µm scale bar).
6. _Pojetaia runnegari_ SMNH Mo185040, magnification of lateral surface, showing laminar crystalline imprints (200 µm scale bar).
7. _Pojetaia runnegari_ SMNH Mo185041, lateral view (200 µm scale bar).
8. _Pojetaia runnegari_ SMNH Mo185042, lateral view (200 µm scale bar).
9. _Pojetaia runnegari_ SMNH Mo185043 (200 µm scale bar).

Please process following caption:

Figure 4.
Helcionellids from the Shackleton Limestone. (1–5) Davidonia cf. D. corrugata Runnegar in Bengtson et al., 1990. (1–3) Specimen SMNH Mo185044 in
(1) oblique lateral view, (2) apical view, (3) magniﬁcation of apical region in lateral view, showing protoconch and transition to teleoconch; (4) specimen SMNH
Mo185045, oblique view of supra-apical ﬁeld; (5) specimen SMNH Mo185046 lateral view. (6–14) Davidonia rostrata (Zhou and Xiao, 1984), (6, 7) specimen
SMNH Mo185047, (6) lateral view, (7) dorsal view of supra-apical ﬁeld; (8–11) specimen SMNH Mo185048, (8) magniﬁcation of lateral view of parietal train,
showing polygonal crystalline imprints on the side surface, (9) dorsal view of supra-apical ﬁeld, (10) lateral view, (11) magniﬁcation of oblique lateral view of
supra-apical ﬁeld, showing polygonal crystalline imprints; (12) specimen SMNH Mo182501 in lateral view; (13) specimen SMNH Mo182502 in lateral view;
(14) specimen SMNH Mo182503 in lateral view. (15–18) Xianfengella cf. X. yatesi Parkhaev in Gravestock et al., 2001, specimen SMNH Mo185049, (15) dorsal
view, (16) oblique apical view, (17) magniﬁed view of supra-apical ﬁeld showing crystalline imprints, (18) oblique lateral view. (19–21) Protowenella? sp. Runnegar
and Jell, 1976 specimen SMNH Mo185050, (19) lateral view, (20) dorsal view, (21) apical view. (22–28) Anuliconus sp. Parkhaev in Gravestock et al. (2001), (22–24)
specimen SMNH Mo185051, (23) lateral view, (22) magniﬁcation of apex in lateral view, (24) apertural view; (25, 26) specimen SMNH Mo185052, (25) lateral view, (26)
apical view; (27, 28) specimen SMNH Mo185053, (27) lateral view, (28) apical view. (3, 10, 11, 17, 22, 24) Scale bars = 100 µm; all others, scale bars = 200 µm.
'''
import ollama

stream = ollama.chat(
    model='llama3',
    messages=[{'role': 'user', 'content': 'Why is the sky blue?'}],
    stream=True,
)

for chunk in stream:
  print(chunk['message']['content'], end='', flush=True)

#import ollama

response = ollama.chat(model='llama3', messages=[
{
    'role': 'user',
    'content': test_txt,
},
])

print( response['message']['content'] )

