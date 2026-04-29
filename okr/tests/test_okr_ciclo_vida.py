from odoo.exceptions import ValidationError
from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestOKRCicloDeVida(TransactionCase):
    """
    Valida el ciclo de vida completo de un OKR:
    creación de OKR padre/hijo, vinculación de objetivos con restricciones
    de cadencia, gestión de Key Results y motor de estados.

    Guion funcional de referencia: flujo de gestión de OKRs individuales.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.user_responsable = cls.env["res.users"].create(
            {
                "name": "Soporte ADHOC",
                "login": "soporte_adhoc_okr_test@test.com",
                "email": "soporte_adhoc_okr_test@test.com",
            }
        )

        # OKR maestro: anual, nivel individual (el nivel raíz debe ser yearly)
        cls.okr_anual = cls.env["okr"].create(
            {
                "name": "OKR-test",
                "level": "individual",
                "cadence": "yearly",
                "year": "2026",
                "in_charge_id": cls.user_responsable.id,
            }
        )

        # OKR hijo con cadencia Q2 (válido: su padre es yearly)
        cls.okr_q2 = cls.env["okr"].create(
            {
                "name": "OKR-test-Q2",
                "level": "individual",
                "cadence": "q2",
                "parent_id": cls.okr_anual.id,
                "in_charge_id": cls.user_responsable.id,
            }
        )

    # ------------------------------------------------------------------ #
    # 1. Creación del OKR maestro                                         #
    # ------------------------------------------------------------------ #

    def test_01_creacion_okr_anual_individual(self):
        """Paso 1: crear OKR maestro anual de nivel individual."""
        self.assertEqual(self.okr_anual.name, "OKR-test")
        self.assertEqual(self.okr_anual.level, "individual")
        self.assertEqual(self.okr_anual.cadence, "yearly")
        self.assertEqual(self.okr_anual.year, "2026")
        self.assertEqual(self.okr_anual.in_charge_id, self.user_responsable)

    def test_02_okr_trimestral_sin_padre_lanza_error(self):
        """Restricción: un OKR trimestral sin padre no puede existir."""
        with self.assertRaises(ValidationError):
            self.env["okr"].create(
                {
                    "name": "OKR-sin-padre-q1",
                    "level": "individual",
                    "cadence": "q1",
                }
            )

    # ------------------------------------------------------------------ #
    # 2. Restricciones de cadencia entre OKR padre e hijo                 #
    # ------------------------------------------------------------------ #

    def test_03_okr_anual_con_padre_trimestral_lanza_error(self):
        """
        Video minuto 0:44: intentar crear un hijo con cadencia anual
        cuyo padre tiene cadencia trimestral debe lanzar ValidationError.
        """
        with self.assertRaises(ValidationError):
            self.env["okr"].create(
                {
                    "name": "OKR-yearly-hijo-de-q2",
                    "level": "individual",
                    "cadence": "yearly",
                    "parent_id": self.okr_q2.id,
                }
            )

    def test_04_okr_hijo_con_cadencia_diferente_al_padre_trimestral_lanza_error(self):
        """
        Restricción de cadencia: un hijo con cadencia Q3 cuyo padre
        es Q2 debe lanzar ValidationError.
        """
        with self.assertRaises(ValidationError):
            self.env["okr"].create(
                {
                    "name": "OKR-q3-hijo-de-q2",
                    "level": "individual",
                    "cadence": "q3",
                    "parent_id": self.okr_q2.id,
                }
            )

    def test_05_relacion_padre_hijo_okr(self):
        """Verificar que el OKR hijo está correctamente vinculado al padre."""
        self.assertEqual(self.okr_q2.parent_id, self.okr_anual)
        self.assertIn(self.okr_q2, self.okr_anual.child_ids)

    # ------------------------------------------------------------------ #
    # 3. Fechas calculadas del OKR anual                                  #
    # ------------------------------------------------------------------ #

    def test_06_fechas_okr_anual_calculadas_correctamente(self):
        """Verificar que las fechas del OKR anual 2026 son correctas."""
        self.assertTrue(self.okr_anual.start_date)
        self.assertTrue(self.okr_anual.end_date)
        self.assertEqual(self.okr_anual.start_date.year, 2026)
        self.assertEqual(self.okr_anual.end_date.year, 2026)
        self.assertEqual(self.okr_anual.start_date.month, 1)
        self.assertEqual(self.okr_anual.end_date.month, 12)

    # ------------------------------------------------------------------ #
    # 4. Creación de Objetivos y restricciones de cadencia                #
    # ------------------------------------------------------------------ #

    def test_07_crear_objetivo_cadencia_q2_en_okr_anual(self):
        """
        Video minuto 1:25: crear un objetivo con cadencia Q2
        vinculado a un OKR anual es válido.
        """
        objetivo = self.env["okr.objective"].create(
            {
                "name": "Objetivo-test",
                "description": "Objetivo de prueba vinculado a OKR anual",
                "type": "aspirational",
                "cadence": "q2",
                "okr_id": self.okr_anual.id,
                "in_charge_id": self.user_responsable.id,
            }
        )
        self.assertTrue(objetivo.id)
        self.assertEqual(objetivo.okr_id, self.okr_anual)
        self.assertEqual(objetivo.type, "aspirational")
        self.assertEqual(objetivo.cadence, "q2")

    def test_08_objetivo_yearly_en_okr_trimestral_lanza_error(self):
        """
        Video minuto 1:25: un objetivo con cadencia anual vinculado
        a un OKR trimestral debe lanzar ValidationError.
        """
        with self.assertRaises(ValidationError):
            self.env["okr.objective"].create(
                {
                    "name": "Objetivo-yearly-en-q2",
                    "description": "Objetivo con cadencia incompatible",
                    "type": "committed",
                    "cadence": "yearly",
                    "okr_id": self.okr_q2.id,
                }
            )

    def test_09_objetivo_cadencia_diferente_a_okr_trimestral_lanza_error(self):
        """
        Restricción: un objetivo Q3 vinculado a un OKR Q2
        debe lanzar ValidationError.
        """
        with self.assertRaises(ValidationError):
            self.env["okr.objective"].create(
                {
                    "name": "Objetivo-q3-en-okr-q2",
                    "description": "Objetivo con cadencia Q3 incompatible con OKR Q2",
                    "type": "committed",
                    "cadence": "q3",
                    "okr_id": self.okr_q2.id,
                }
            )

    # ------------------------------------------------------------------ #
    # 5. Ciclo de vida del Key Result                                     #
    # ------------------------------------------------------------------ #

    def test_10_ciclo_de_vida_key_result_draft_activo_cancelado(self):
        """
        Video minuto 2:00–2:40: ciclo completo de un Key Result:
        borrador → activo → cancelado.
        """
        objetivo = self.env["okr.objective"].create(
            {
                "name": "Objetivo para KR ciclo de vida",
                "description": "Objetivo que contiene el KR de prueba",
                "type": "committed",
                "cadence": "q2",
                "okr_id": self.okr_anual.id,
            }
        )
        kr = self.env["okr.key_result"].create(
            {
                "name": "Key-result",
                "description": "KR",
                "weight": 0.2,
                "target": 100.0,
                "objective_id": objetivo.id,
            }
        )

        # Estado inicial debe ser 'draft'
        self.assertEqual(kr.state, "draft")

        # Confirmar: draft → active
        kr.set_active()
        self.assertEqual(kr.state, "active")

        # Actualizar progreso
        kr.write({"result": 10.0})
        self.assertEqual(kr.result, 10.0)

        # Cancelar: active → cancelled (video minuto 2:40)
        kr.set_cancelled()
        self.assertEqual(kr.state, "cancelled")

    # ------------------------------------------------------------------ #
    # 6. Validaciones de datos del Key Result                             #
    # ------------------------------------------------------------------ #

    def test_11_peso_y_meta_key_result_almacenados_correctamente(self):
        """Validar que el peso y la meta del KR se almacenan correctamente."""
        objetivo = self.env["okr.objective"].create(
            {
                "name": "Objetivo peso/meta",
                "description": "Objetivo para validar peso y meta del KR",
                "type": "committed",
                "cadence": "q2",
                "okr_id": self.okr_anual.id,
            }
        )
        kr = self.env["okr.key_result"].create(
            {
                "name": "KR peso/meta",
                "description": "KR para validar campos numéricos",
                "weight": 0.2,
                "target": 100.0,
                "objective_id": objetivo.id,
            }
        )
        self.assertEqual(kr.weight, 0.2)
        self.assertEqual(kr.target, 100.0)

    def test_12_peso_fuera_de_rango_lanza_error(self):
        """El peso de un KR debe estar entre 0 y 1 (0–100 %)."""
        objetivo = self.env["okr.objective"].create(
            {
                "name": "Objetivo peso-invalido",
                "description": "Objetivo para validar peso inválido",
                "type": "committed",
                "cadence": "q2",
                "okr_id": self.okr_anual.id,
            }
        )
        with self.assertRaises(ValidationError):
            self.env["okr.key_result"].create(
                {
                    "name": "KR-peso-invalido",
                    "description": "KR con peso mayor a 1",
                    "weight": 1.5,
                    "target": 100.0,
                    "objective_id": objetivo.id,
                }
            )

    def test_13_suma_de_pesos_que_excede_100_lanza_error(self):
        """
        Restricción: la suma de pesos de los KR de un objetivo
        no puede superar el 100 % (1.0).
        """
        objetivo = self.env["okr.objective"].create(
            {
                "name": "Objetivo suma-pesos",
                "description": "Objetivo para validar suma total de pesos",
                "type": "committed",
                "cadence": "q2",
                "okr_id": self.okr_anual.id,
            }
        )
        self.env["okr.key_result"].create(
            {
                "name": "KR-A",
                "description": "Primer KR con peso 70%",
                "weight": 0.7,
                "target": 100.0,
                "objective_id": objetivo.id,
            }
        )
        with self.assertRaises(ValidationError):
            self.env["okr.key_result"].create(
                {
                    "name": "KR-B",
                    "description": "Segundo KR que lleva la suma por encima del 100%",
                    "weight": 0.5,
                    "target": 100.0,
                    "objective_id": objetivo.id,
                }
            )

    # ------------------------------------------------------------------ #
    # 7. Cálculo del resultado del Objetivo                               #
    # ------------------------------------------------------------------ #

    def test_14_calculo_resultado_objetivo_promedio_ponderado(self):
        """
        Verificar que el resultado del objetivo es el promedio ponderado
        del progreso de sus KRs activos.

        Fórmula: sum(result/target * weight) / sum(weight)
        Esperado: (50/100 * 0.6 + 100/100 * 0.4) / (0.6 + 0.4) = 0.70
        """
        objetivo = self.env["okr.objective"].create(
            {
                "name": "Objetivo calculo-resultado",
                "description": "Objetivo para validar cálculo de resultado ponderado",
                "type": "committed",
                "cadence": "q2",
                "okr_id": self.okr_anual.id,
            }
        )
        kr1 = self.env["okr.key_result"].create(
            {
                "name": "KR-1",
                "description": "KR con peso 60% para cálculo",
                "weight": 0.6,
                "target": 100.0,
                "objective_id": objetivo.id,
            }
        )
        kr2 = self.env["okr.key_result"].create(
            {
                "name": "KR-2",
                "description": "KR con peso 40% para cálculo",
                "weight": 0.4,
                "target": 100.0,
                "objective_id": objetivo.id,
            }
        )

        # Sin KRs activos el resultado debe ser 0
        self.assertEqual(objetivo.result, 0.0)

        # Activar KRs y asignar resultados para disparar el recompute
        kr1.set_active()
        kr2.set_active()
        kr1.write({"result": 50.0})
        kr2.write({"result": 100.0})

        expected = (50.0 / 100.0 * 0.6 + 100.0 / 100.0 * 0.4) / (0.6 + 0.4)
        self.assertAlmostEqual(objetivo.result, expected, places=5)

    def test_15_resultado_objetivo_sin_krs_activos_es_cero(self):
        """
        Si todos los KR del objetivo están en estado 'draft',
        el resultado del objetivo debe ser 0.
        """
        objetivo = self.env["okr.objective"].create(
            {
                "name": "Objetivo sin KRs activos",
                "description": "Objetivo para validar resultado cero sin KRs activos",
                "type": "committed",
                "cadence": "q2",
                "okr_id": self.okr_anual.id,
            }
        )
        self.env["okr.key_result"].create(
            {
                "name": "KR-draft",
                "description": "KR en borrador",
                "weight": 1.0,
                "target": 100.0,
                "result": 80.0,
                "objective_id": objetivo.id,
            }
        )
        # El KR está en draft, no debe contribuir al resultado
        self.assertEqual(objetivo.result, 0.0)
