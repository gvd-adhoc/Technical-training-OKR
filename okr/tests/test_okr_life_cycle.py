from odoo.exceptions import AccessError, ValidationError
from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestOKRLifeCycle(TransactionCase):
    """
    Validate the full OKR lifecycle:
    parent/child OKR creation, objective linking with cadence restrictions,
    Key Result management, and the state engine.

    Functional reference scenario: individual OKR management flow.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.responsible_user = cls.env["res.users"].create(
            {
                "name": "Soporte ADHOC",
                "login": "soporte_adhoc_okr_test@test.com",
                "email": "soporte_adhoc_okr_test@test.com",
            }
        )

        # Master OKR: yearly, individual level (root OKRs must be yearly)
        cls.yearly_okr = cls.env["okr"].create(
            {
                "name": "OKR-test",
                "level": "individual",
                "cadence": "yearly",
                "year": "2026",
                "in_charge_id": cls.responsible_user.id,
            }
        )

        # Child OKR with Q2 cadence (valid because its parent is yearly)
        cls.okr_q2 = cls.env["okr"].create(
            {
                "name": "OKR-test-Q2",
                "level": "individual",
                "cadence": "q2",
                "parent_id": cls.yearly_okr.id,
                "in_charge_id": cls.responsible_user.id,
            }
        )

    # ------------------------------------------------------------------ #
    # 1. Master OKR creation                                              #
    # ------------------------------------------------------------------ #

    def test_01_create_yearly_individual_okr(self):
        """Step 1: create a yearly master OKR at individual level."""
        self.assertEqual(self.yearly_okr.name, "OKR-test")
        self.assertEqual(self.yearly_okr.level, "individual")
        self.assertEqual(self.yearly_okr.cadence, "yearly")
        self.assertEqual(self.yearly_okr.year, "2026")
        self.assertEqual(self.yearly_okr.in_charge_id, self.responsible_user)

    def test_02_quarterly_okr_without_parent_raises_error(self):
        """Restriction: a quarterly OKR cannot exist without a parent."""
        with self.assertRaises(ValidationError):
            self.env["okr"].create(
                {
                    "name": "OKR-sin-padre-q1",
                    "level": "individual",
                    "cadence": "q1",
                }
            )

    # ------------------------------------------------------------------ #
    # 2. Cadence restrictions between parent and child OKRs               #
    # ------------------------------------------------------------------ #

    def test_03_yearly_okr_with_quarterly_parent_raises_error(self):
        """
        Video minute 0:44: trying to create a yearly child OKR
        whose parent has quarterly cadence must raise ValidationError.
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

    def test_04_child_okr_with_different_quarterly_parent_cadence_raises_error(self):
        """
        Cadence restriction: a Q3 child whose parent is Q2
        must raise ValidationError.
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

    def test_05_okr_parent_child_relationship(self):
        """Verify that the child OKR is correctly linked to the parent."""
        self.assertEqual(self.okr_q2.parent_id, self.yearly_okr)
        self.assertIn(self.okr_q2, self.yearly_okr.child_ids)

    # ------------------------------------------------------------------ #
    # 3. Computed dates for the yearly OKR                                 #
    # ------------------------------------------------------------------ #

    def test_06_yearly_okr_dates_are_computed_correctly(self):
        """Verify that the dates for the 2026 yearly OKR are correct."""
        self.assertTrue(self.yearly_okr.start_date)
        self.assertTrue(self.yearly_okr.end_date)
        self.assertEqual(self.yearly_okr.start_date.year, 2026)
        self.assertEqual(self.yearly_okr.end_date.year, 2026)
        self.assertEqual(self.yearly_okr.start_date.month, 1)
        self.assertEqual(self.yearly_okr.end_date.month, 12)

    # ------------------------------------------------------------------ #
    # 4. Objective creation and cadence restrictions                       #
    # ------------------------------------------------------------------ #

    def test_07_create_q2_objective_in_yearly_okr(self):
        """
        Video minute 1:25: creating a Q2 objective linked
        to a yearly OKR is valid.
        """
        objective = self.env["okr.objective"].create(
            {
                "name": "Objetivo-test",
                "description": "Objetivo de prueba vinculado a OKR anual",
                "type": "aspirational",
                "cadence": "q2",
                "okr_id": self.yearly_okr.id,
                "in_charge_id": self.responsible_user.id,
            }
        )
        self.assertTrue(objective.id)
        self.assertEqual(objective.okr_id, self.yearly_okr)
        self.assertEqual(objective.type, "aspirational")
        self.assertEqual(objective.cadence, "q2")

    def test_08_yearly_objective_in_quarterly_okr_raises_error(self):
        """
        Video minute 1:25: a yearly objective linked to a
        quarterly OKR must raise ValidationError.
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

    def test_09_objective_with_different_quarterly_okr_cadence_raises_error(self):
        """
        Restriction: a Q3 objective linked to a Q2 OKR
        must raise ValidationError.
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
    # 5. Key Result lifecycle                                             #
    # ------------------------------------------------------------------ #

    def test_10_key_result_lifecycle_draft_active_cancelled(self):
        """
        Video minute 2:00-2:40: full Key Result lifecycle:
        draft -> active -> cancelled.
        """
        objective = self.env["okr.objective"].create(
            {
                "name": "Objetivo para KR ciclo de vida",
                "description": "Objetivo que contiene el KR de prueba",
                "type": "committed",
                "cadence": "q2",
                "okr_id": self.yearly_okr.id,
            }
        )
        kr = self.env["okr.key_result"].create(
            {
                "name": "Key-result",
                "description": "KR",
                "weight": 0.2,
                "target": 100.0,
                "objective_id": objective.id,
            }
        )

        # Initial state must be 'draft'
        self.assertEqual(kr.state, "draft")

        # Confirm: draft -> active
        kr.set_active()
        self.assertEqual(kr.state, "active")

        # Update progress
        kr.write({"result": 10.0})
        self.assertEqual(kr.result, 10.0)

        # Cancel: active -> cancelled (video minute 2:40)
        kr.set_cancelled()
        self.assertEqual(kr.state, "cancelled")

    # ------------------------------------------------------------------ #
    # 6. Key Result data validations                                      #
    # ------------------------------------------------------------------ #

    def test_11_key_result_weight_and_target_are_stored_correctly(self):
        """Validate that the KR weight and target are stored correctly."""
        objective = self.env["okr.objective"].create(
            {
                "name": "Objetivo peso/meta",
                "description": "Objetivo para validar peso y meta del KR",
                "type": "committed",
                "cadence": "q2",
                "okr_id": self.yearly_okr.id,
            }
        )
        kr = self.env["okr.key_result"].create(
            {
                "name": "KR peso/meta",
                "description": "KR para validar campos numéricos",
                "weight": 0.2,
                "target": 100.0,
                "objective_id": objective.id,
            }
        )
        self.assertEqual(kr.weight, 0.2)
        self.assertEqual(kr.target, 100.0)

    def test_12_out_of_range_weight_raises_error(self):
        """A KR weight must be between 0 and 1 (0-100%)."""
        objective = self.env["okr.objective"].create(
            {
                "name": "Objetivo peso-invalido",
                "description": "Objetivo para validar peso inválido",
                "type": "committed",
                "cadence": "q2",
                "okr_id": self.yearly_okr.id,
            }
        )
        with self.assertRaises(ValidationError):
            self.env["okr.key_result"].create(
                {
                    "name": "KR-peso-invalido",
                    "description": "KR con peso mayor a 1",
                    "weight": 1.5,
                    "target": 100.0,
                    "objective_id": objective.id,
                }
            )

    def test_13_weight_sum_exceeding_100_raises_error(self):
        """
        Restriction: the sum of KR weights for an objective
        cannot exceed 100% (1.0).
        """
        objective = self.env["okr.objective"].create(
            {
                "name": "Objetivo suma-pesos",
                "description": "Objetivo para validar suma total de pesos",
                "type": "committed",
                "cadence": "q2",
                "okr_id": self.yearly_okr.id,
            }
        )
        self.env["okr.key_result"].create(
            {
                "name": "KR-A",
                "description": "Primer KR con peso 70%",
                "weight": 0.7,
                "target": 100.0,
                "objective_id": objective.id,
            }
        )
        with self.assertRaises(ValidationError):
            self.env["okr.key_result"].create(
                {
                    "name": "KR-B",
                    "description": "Segundo KR que lleva la suma por encima del 100%",
                    "weight": 0.5,
                    "target": 100.0,
                    "objective_id": objective.id,
                }
            )

    # ------------------------------------------------------------------ #
    # 7. Objective result calculation                                     #
    # ------------------------------------------------------------------ #

    def test_14_objective_result_weighted_average_calculation(self):
        """
        Verify that the objective result is the weighted average
        of its active KRs' progress.

        Formula: sum(result/target * weight) / sum(weight)
        Expected: (50/100 * 0.6 + 100/100 * 0.4) / (0.6 + 0.4) = 0.70
        """
        objective = self.env["okr.objective"].create(
            {
                "name": "Objetivo calculo-resultado",
                "description": "Objetivo para validar cálculo de resultado ponderado",
                "type": "committed",
                "cadence": "q2",
                "okr_id": self.yearly_okr.id,
            }
        )
        kr1 = self.env["okr.key_result"].create(
            {
                "name": "KR-1",
                "description": "KR con peso 60% para cálculo",
                "weight": 0.6,
                "target": 100.0,
                "objective_id": objective.id,
            }
        )
        kr2 = self.env["okr.key_result"].create(
            {
                "name": "KR-2",
                "description": "KR con peso 40% para cálculo",
                "weight": 0.4,
                "target": 100.0,
                "objective_id": objective.id,
            }
        )

        # Without active KRs, the result must be 0
        self.assertEqual(objective.result, 0.0)

        # Activate KRs and assign results to trigger the recompute
        kr1.set_active()
        kr2.set_active()
        kr1.write({"result": 50.0})
        kr2.write({"result": 100.0})

        expected = (50.0 / 100.0 * 0.6 + 100.0 / 100.0 * 0.4) / (0.6 + 0.4)
        self.assertAlmostEqual(objective.result, expected, places=5)

    def test_15_objective_result_without_active_krs_is_zero(self):
        """
        If all objective KRs are in 'draft' state,
        the objective result must be 0.
        """
        objective = self.env["okr.objective"].create(
            {
                "name": "Objetivo sin KRs activos",
                "description": "Objetivo para validar resultado cero sin KRs activos",
                "type": "committed",
                "cadence": "q2",
                "okr_id": self.yearly_okr.id,
            }
        )
        self.env["okr.key_result"].create(
            {
                "name": "KR-draft",
                "description": "KR en borrador",
                "weight": 1.0,
                "target": 100.0,
                "result": 80.0,
                "objective_id": objective.id,
            }
        )
        # The KR is in draft, so it must not contribute to the result
        self.assertEqual(objective.result, 0.0)

    def test_16_zero_target_raises_error(self):
        """A KR target must be greater than zero to avoid invalid divisions."""
        objective = self.env["okr.objective"].create(
            {
                "name": "Objetivo target cero",
                "description": "Objetivo para validar target inválido",
                "type": "committed",
                "cadence": "q2",
                "okr_id": self.yearly_okr.id,
            }
        )
        with self.assertRaises(ValidationError):
            self.env["okr.key_result"].create(
                {
                    "name": "KR target cero",
                    "description": "KR con target inválido",
                    "weight": 1.0,
                    "target": 0.0,
                    "objective_id": objective.id,
                }
            )

    def test_17_objective_result_recomputes_by_state_target_and_weight(self):
        """The result must reflect changes in KR state, target, and weight."""
        objective = self.env["okr.objective"].create(
            {
                "name": "Objetivo recompute",
                "description": "Objetivo para validar recomputes",
                "type": "committed",
                "cadence": "q2",
                "okr_id": self.yearly_okr.id,
            }
        )
        kr = self.env["okr.key_result"].create(
            {
                "name": "KR recompute",
                "description": "KR para validar recomputes",
                "weight": 1.0,
                "target": 100.0,
                "result": 50.0,
                "objective_id": objective.id,
            }
        )

        self.assertEqual(objective.result, 0.0)

        kr.set_active()
        self.assertAlmostEqual(objective.result, 0.5, places=5)

        kr.write({"target": 200.0})
        self.assertAlmostEqual(objective.result, 0.25, places=5)

        kr.write({"weight": 0.5})
        self.assertAlmostEqual(objective.result, 0.25, places=5)

        kr.set_cancelled()
        self.assertEqual(objective.result, 0.0)

    # ------------------------------------------------------------------ #
    # 8. Automation, dates, deletion, and security                         #
    # ------------------------------------------------------------------ #

    def test_18_cron_closes_key_results_from_expired_objectives(self):
        """The cron must mark KRs from expired objectives as done."""
        objective = self.env["okr.objective"].create(
            {
                "name": "Objetivo vencido Q1",
                "description": "Objetivo vencido para validar cron",
                "type": "committed",
                "cadence": "q1",
                "okr_id": self.yearly_okr.id,
            }
        )
        kr = self.env["okr.key_result"].create(
            {
                "name": "KR a cerrar",
                "description": "KR para validar cron",
                "weight": 1.0,
                "target": 100.0,
                "objective_id": objective.id,
            }
        )
        kr.set_active()

        self.env["okr.objective"]._cron_close_finished_objectives()

        self.assertEqual(kr.state, "done")

    def test_19_deleting_objective_unlinks_and_cancels_key_results(self):
        """When deleting an objective, its KRs are unlinked and cancelled."""
        objective = self.env["okr.objective"].create(
            {
                "name": "Objetivo a borrar",
                "description": "Objetivo para validar unlink",
                "type": "committed",
                "cadence": "q2",
                "okr_id": self.yearly_okr.id,
            }
        )
        kr = self.env["okr.key_result"].create(
            {
                "name": "KR objetivo borrado",
                "description": "KR para validar unlink",
                "weight": 1.0,
                "target": 100.0,
                "objective_id": objective.id,
            }
        )

        objective.unlink()

        self.assertFalse(kr.objective_id)
        self.assertEqual(kr.state, "cancelled")

    def test_20_deleting_okr_unlinks_objectives_and_children(self):
        """When deleting an OKR, its objectives and children must be unlinked."""
        parent_okr = self.env["okr"].create(
            {
                "name": "OKR padre unlink",
                "level": "individual",
                "cadence": "yearly",
                "year": "2026",
            }
        )
        objective = self.env["okr.objective"].create(
            {
                "name": "Objetivo OKR borrado",
                "description": "Objetivo para validar unlink de OKR",
                "type": "committed",
                "cadence": "q2",
                "okr_id": parent_okr.id,
            }
        )
        child_okr = self.env["okr"].create(
            {
                "name": "OKR hijo unlink",
                "level": "individual",
                "cadence": "q3",
                "parent_id": parent_okr.id,
            }
        )

        parent_okr.unlink()

        self.assertFalse(objective.okr_id)
        self.assertFalse(child_okr.parent_id)

    def test_21_standalone_quarterly_objective_is_valid_and_computes_dates(self):
        """A standalone quarterly objective is valid and computes its period."""
        objective = self.env["okr.objective"].create(
            {
                "name": "Objetivo suelto Q4",
                "description": "Objetivo sin OKR asociado",
                "type": "aspirational",
                "cadence": "q4",
            }
        )

        self.assertFalse(objective.okr_id)
        self.assertTrue(objective.start_date)
        self.assertTrue(objective.end_date)

    def test_22_q2_child_okr_dates_are_computed_correctly(self):
        """A Q2 child OKR must use its own cadence and the parent's year."""
        self.assertEqual(self.okr_q2.start_date.year, 2026)
        self.assertEqual(self.okr_q2.end_date.year, 2026)
        self.assertEqual(self.okr_q2.start_date.month, 4)
        self.assertEqual(self.okr_q2.end_date.month, 6)

    def test_23_okr_user_cannot_create_okr(self):
        """The User group can read/write owned records, but cannot create OKRs."""
        user = self.env["res.users"].create(
            {
                "name": "Usuario OKR",
                "login": "usuario_okr_test@test.com",
                "email": "usuario_okr_test@test.com",
                "group_ids": [
                    (
                        6,
                        0,
                        [
                            self.env.ref("base.group_user").id,
                            self.env.ref("okr.group_okr_user").id,
                        ],
                    )
                ],
            }
        )

        with self.assertRaises(AccessError):
            self.env["okr"].with_user(user).create(
                {
                    "name": "OKR usuario sin permiso",
                    "level": "individual",
                    "cadence": "yearly",
                    "year": "2026",
                }
            )

    def test_24_okr_manager_can_create_okr(self):
        """The Manager group can create OKRs."""
        manager = self.env["res.users"].create(
            {
                "name": "Manager OKR",
                "login": "manager_okr_test@test.com",
                "email": "manager_okr_test@test.com",
                "group_ids": [
                    (
                        6,
                        0,
                        [
                            self.env.ref("base.group_user").id,
                            self.env.ref("okr.group_okr_manager").id,
                        ],
                    )
                ],
            }
        )

        okr = (
            self.env["okr"]
            .with_user(manager)
            .create(
                {
                    "name": "OKR manager",
                    "level": "individual",
                    "cadence": "yearly",
                    "year": "2026",
                }
            )
        )

        self.assertTrue(okr.id)
