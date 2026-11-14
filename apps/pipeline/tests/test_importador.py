"""Parte pura del importador: puntuación, filtro de licencias, reverificación (con red simulada) y manifiesto."""

import json
from pathlib import Path

import pytest
from PIL import Image

from taller6mm_pipeline.importador import hoja, manifiesto, puntuacion, sketchfab
from taller6mm_pipeline.importador.red import ClienteHttp, ErrorHttp

RAIZ = Path(__file__).resolve().parents[3]
TERMINOS = json.loads((RAIZ / "catalogo" / "importador-terminos.json").read_text(encoding="utf-8"))


def anot(
    nombre: str,
    *,
    licencia: str = "by",
    etiquetas: tuple[str, ...] = (),
    caras: int | None = 10000,
    uid="u1",
    autor="A",
):
    return puntuacion.Anotacion(
        uid, nombre, etiquetas, licencia, autor, f"https://sketchfab.com/3d-models/{uid}", caras
    )


def pts(nombre: str, pieza: str, **kw):
    return puntuacion.puntuar(anot(nombre, **kw), TERMINOS["piezas"][pieza], TERMINOS)


def test_normalizar_y_contiene():
    assert puntuacion.normalizar("M-LOK Handguard_v2") == "m lok handguard v2"
    assert puntuacion.contiene("ar15 m lok handguard", "M-LOK")
    assert not puntuacion.contiene("mlokx", "mlok")


def test_licencia_no_admitida_descarta():
    assert pts("M-LOK handguard AR-15", "guardamanos-mlok") is not None
    for lic in ("by-nc", "by-sa", "by-nc-sa", "by-nd", ""):
        assert pts("M-LOK handguard AR-15", "guardamanos-mlok", licencia=lic) is None
    assert pts("M-LOK handguard AR-15", "guardamanos-mlok", licencia="cc0") is not None


def test_exclusiones_y_sin_coincidencia():
    assert pts("Magpul STR stock minecraft", "culata-magpul-str") is None
    assert pts("Coffee mug", "culata-magpul-str") is None
    assert pts("ACOG red dot", "red-dot") is None


def test_termino_debil_exige_contexto():
    assert pts("Stock", "culata-magpul-str") is None
    assert pts("Rifle stock", "culata-magpul-str") is not None
    assert pts("Stock", "culata-magpul-str", etiquetas=("ar-15",)) is not None


def test_nombre_pesa_mas_que_etiqueta_y_caras_razonables():
    en_nombre = pts("Magpul STR stock", "culata-magpul-str")
    en_etiqueta = pts("Thing", "culata-magpul-str", etiquetas=("magpul str",))
    assert en_nombre and en_etiqueta and en_nombre.puntos > en_etiqueta.puntos
    razonable = pts("Magpul STR stock", "culata-magpul-str", caras=8000)
    enorme = pts("Magpul STR stock", "culata-magpul-str", caras=900000)
    assert razonable and enorme and razonable.puntos > enorme.puntos
    assert pts("Magpul STR stock", "culata-magpul-str", caras=None) is not None


def test_mejores_orden_estable_y_sin_duplicados():
    lote = [
        anot("Magpul STR stock", uid="b", autor="X"),
        anot("Magpul STR stock", uid="a", autor="X"),  # mismo autor y nombre: duplicado
        anot("Magpul CTR stock", uid="c", autor="Y"),
        anot("Magpul MOE stock", uid="d", autor="Z", licencia="by-nc"),
    ]
    sel = puntuacion.mejores(lote, TERMINOS["piezas"]["culata-magpul-str"], TERMINOS, n=5)
    assert [p.anotacion.uid for p in sel] == ["a", "c"]
    assert len(puntuacion.mejores(lote, TERMINOS["piezas"]["culata-magpul-str"], TERMINOS, n=1)) == 1


def test_desde_objaverse():
    a = puntuacion.Anotacion.desde_objaverse(
        "x", {"name": "N", "license": "by", "faceCount": 5, "tags": [{"name": "t"}], "user": {"displayName": "D"}}
    )
    assert (a.nombre, a.autor, a.caras, a.etiquetas) == ("N", "D", 5, ("t",))


def test_tabla_de_terminos_es_coherente():
    ar = json.loads((RAIZ / "catalogo" / "ar-m4.json").read_text(encoding="utf-8"))
    ids = {e["id"] for e in ar["elementos"]}
    assert set(TERMINOS["licencias_admitidas"]) == {"cc0", "by"}
    for clave, pieza in TERMINOS["piezas"].items():
        assert pieza["elemento"] in ids, clave
        assert pieza["fuertes"], clave


class Falso:
    def __init__(self, respuestas):
        self.respuestas = respuestas
        self.peticiones: list[str] = []

    def obtener(self, url):
        self.peticiones.append(url)
        r = self.respuestas[url]
        if isinstance(r, Exception):
            raise r
        return json.dumps(r).encode()

    def descargar(self, url, destino, *, max_bytes):  # pragma: no cover - no se usa aquí
        raise AssertionError


def ficha(slug):
    return {
        "name": "AR stock",
        "viewerUrl": "https://sketchfab.com/3d-models/z",
        "user": {"displayName": "Autor"},
        "license": {"slug": slug},
    }


@pytest.mark.parametrize(
    ("slug", "ok", "estado"),
    [
        ("by", True, "ok"),
        ("cc0", True, "ok"),
        ("by-nc", False, "licencia_cambiada"),
        ("by-nd", False, "licencia_cambiada"),
        ("by-sa", False, "licencia_cambiada"),
    ],
)
def test_reverificar_licencias(slug, ok, estado):
    c = Falso({f"{sketchfab.API}/z": ficha(slug)})
    v = sketchfab.verificar("z", c)
    assert (v.ok, v.estado) == (ok, estado)
    if ok:
        assert v.licencia in manifiesto.LICENCIAS_OK and v.autor == "Autor"


def test_reverificar_borrado_y_errores():
    url = f"{sketchfab.API}/z"
    assert sketchfab.verificar("z", Falso({url: ErrorHttp(404, url)})).estado == "borrado"
    v = sketchfab.verificar("z", Falso({url: ErrorHttp(429, url)}))
    assert not v.ok and v.estado == "error"
    assert sketchfab.verificar("z", Falso({url: {"name": "x"}})).estado == "error"


def test_atribucion():
    t = sketchfab.atribucion(
        "T", "A", "CC BY 4.0", "https://creativecommons.org/licenses/by/4.0/", "https://sketchfab.com/3d-models/z"
    )
    assert t.startswith('"T" de A, CC BY 4.0 (')


def test_ritmo_minimo_entre_peticiones():
    t = [0.0]
    dormidos: list[float] = []
    c = ClienteHttp(dormir=lambda s: (dormidos.append(s), t.__setitem__(0, t[0] + s)), reloj=lambda: t[0])
    c._esperar()
    t[0] += 0.3
    c._esperar()
    assert dormidos == [pytest.approx(0.7)]


def test_red_rechaza_http_plano():
    with pytest.raises(ValueError, match="https"):
        ClienteHttp()._abrir("http://example.com")


MEDIDAS_OK = {"mallas": 2, "triangulos": 5000, "bbox_m": [0.1, 0.05, 0.02], "texto_sospechoso": []}


def test_veredicto_auto():
    f = manifiesto.veredicto_auto
    assert f(verificacion_ok=False, motivo_verificacion="borrado", descarga_ok=False, medidas=None) == (
        "descartado",
        "borrado",
    )
    assert f(verificacion_ok=True, motivo_verificacion="", descarga_ok=False, medidas=None)[0] == "descartado"
    assert f(verificacion_ok=True, motivo_verificacion="", descarga_ok=True, medidas={"error": "x"})[0] == "descartado"
    assert (
        f(verificacion_ok=True, motivo_verificacion="", descarga_ok=True, medidas={**MEDIDAS_OK, "mallas": 0})[0]
        == "descartado"
    )
    assert (
        f(verificacion_ok=True, motivo_verificacion="", descarga_ok=True, medidas={**MEDIDAS_OK, "triangulos": 9})[0]
        == "descartado"
    )
    assert f(verificacion_ok=True, motivo_verificacion="", descarga_ok=True, medidas=MEDIDAS_OK)[0] == "candidato"
    v, motivo = f(
        verificacion_ok=True,
        motivo_verificacion="",
        descarga_ok=True,
        medidas={**MEDIDAS_OK, "texto_sospechoso": ["logo.png"]},
    )
    assert v == "candidato" and "logo.png" in motivo


def candidato(**kw):
    base = {
        "uid": "u",
        "titulo": "T",
        "autor": "A",
        "url": "https://sketchfab.com/3d-models/u",
        "licencia": "CC BY 4.0",
        "licencia_verificada": "2026-11-14",
        "atribucion": "x",
        "archivo": "assets-src/raw/modelos-cc/u.glb",
        "sha256": "a" * 64,
        "triangulos": 10,
        "puntuacion": 1.0,
        "veredicto": "candidato",
        "motivo": "ok",
        "publicable": False,
    }
    return {**base, **kw}


def test_manifiesto_valida_y_nunca_publicable(tmp_path):
    m = manifiesto.cargar(tmp_path / "no-existe.json")
    manifiesto.registrar(m, "p", "elem", "2026-11-14", [candidato()])
    manifiesto.guardar(tmp_path / "m.json", m)
    assert manifiesto.cargar(tmp_path / "m.json")["piezas"]["p"]["candidatos"][0]["uid"] == "u"
    for malo in (
        {"publicable": True},
        {"veredicto": "genial"},
        {"motivo": ""},
        {"licencia": "CC BY-NC 4.0"},
        {"sha256": "zz"},
        {"triangulos": 0},
        {"atribucion": ""},
    ):
        with pytest.raises(ValueError, match="u"):
            manifiesto.registrar(manifiesto.cargar(tmp_path / "no.json"), "p", "e", "d", [candidato(**malo)])
    with pytest.raises(ValueError, match="esquema"):
        manifiesto.validar({"esquema": "otro", "piezas": {}})


def test_descartado_no_exige_sha(tmp_path):
    m = manifiesto.cargar(tmp_path / "x.json")
    manifiesto.registrar(
        m, "p", "e", "d", [{"uid": "z", "veredicto": "descartado", "motivo": "borrado", "publicable": False}]
    )


def test_hoja_de_contacto(tmp_path):
    png = tmp_path / "a.png"
    Image.new("RGB", (320, 320), (200, 10, 10)).save(png)
    cands = [candidato(), candidato(uid="v", veredicto="descartado", motivo="borrado en Sketchfab")]
    destino = hoja.hoja_contacto(cands, {"u": png}, tmp_path / "s" / "hoja.png", "prueba")
    with Image.open(destino) as im:
        assert im.size[0] == 3 * hoja.CELDA
