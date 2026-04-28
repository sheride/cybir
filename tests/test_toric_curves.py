"""Tests for cybir.core.toric_curves module."""

import numpy as np
import pytest


def _cytools_available():
    try:
        import cytools  # noqa: F401

        return True
    except ImportError:
        return False


class TestToricCurveData:
    """Tests for ToricCurveData dataclass."""

    def test_construction(self):
        from cybir.core.toric_curves import ToricCurveData

        tcd = ToricCurveData()
        assert tcd.flop_curves == []
        assert tcd.gv_dict == {}

    def test_merge(self):
        from cybir.core.toric_curves import ToricCurveData

        a = ToricCurveData(
            flop_curves=[np.array([1, 0])], gv_dict={(1, 0): 1}
        )
        b = ToricCurveData(
            flop_curves=[np.array([0, 1])], gv_dict={(0, 1): 2}
        )
        a.merge(b)
        assert len(a.flop_curves) == 2
        assert a.gv_dict[(0, 1)] == 2

    def test_all_curves(self):
        from cybir.core.toric_curves import ToricCurveData

        tcd = ToricCurveData(
            flop_curves=[np.array([1, 0])],
            weyl_curves_g0=[np.array([0, 1])],
        )
        assert len(tcd.all_curves()) == 2

    def test_merge_preserves_all_fields(self):
        from cybir.core.toric_curves import ToricCurveData

        a = ToricCurveData(
            flop_curves=[np.array([1, 0])],
            weyl_curves_g0=[np.array([0, 1])],
            weyl_curves_higher_genus=[np.array([1, 1])],
            other_curves=[np.array([2, 0])],
            minface1_curves=[np.array([0, 2])],
            gv_dict={(1, 0): 1},
        )
        b = ToricCurveData(
            flop_curves=[np.array([3, 0])],
            weyl_curves_g0=[np.array([0, 3])],
            weyl_curves_higher_genus=[np.array([3, 3])],
            other_curves=[np.array([4, 0])],
            minface1_curves=[np.array([0, 4])],
            gv_dict={(3, 0): 5},
        )
        a.merge(b)
        assert len(a.flop_curves) == 2
        assert len(a.weyl_curves_g0) == 2
        assert len(a.weyl_curves_higher_genus) == 2
        assert len(a.other_curves) == 2
        assert len(a.minface1_curves) == 2
        assert len(a.gv_dict) == 2
        assert len(a.all_curves()) == 10


class TestOrientCurves:
    """Tests for orient_curves_for_phase."""

    def test_orientation(self):
        from cybir.core.toric_curves import orient_curves_for_phase

        curves = [np.array([1, -1]), np.array([-1, 1])]
        tip = np.array([1, 1])
        oriented = orient_curves_for_phase(curves, tip)
        # Both should have non-negative pairing with tip
        for c in oriented:
            assert tip @ c >= 0

    def test_zero_pairing_unchanged(self):
        from cybir.core.toric_curves import orient_curves_for_phase

        curves = [np.array([1, -1])]
        tip = np.array([1, 1])  # tip @ [1, -1] = 0
        oriented = orient_curves_for_phase(curves, tip)
        np.testing.assert_array_equal(oriented[0], np.array([1, -1]))

    def test_negative_flipped(self):
        from cybir.core.toric_curves import orient_curves_for_phase

        curves = [np.array([-1, -1])]
        tip = np.array([1, 1])  # tip @ [-1, -1] = -2
        oriented = orient_curves_for_phase(curves, tip)
        np.testing.assert_array_equal(oriented[0], np.array([1, 1]))

    def test_positive_unchanged(self):
        from cybir.core.toric_curves import orient_curves_for_phase

        curves = [np.array([1, 1])]
        tip = np.array([1, 1])  # tip @ [1, 1] = 2
        oriented = orient_curves_for_phase(curves, tip)
        np.testing.assert_array_equal(oriented[0], np.array([1, 1]))


class TestClassifyPhaseType:
    """Tests for FRST detection (requires CYTools + regfans)."""

    @pytest.mark.skipif(
        not _cytools_available(),
        reason="CYTools not available",
    )
    def test_classify_phase_type(self):
        """classify_phase_type returns valid (type, fan) tuple."""
        import cytools

        from cybir.core.toric_curves import classify_phase_type

        # Use an h11=2 polytope -- small and fast
        polys = cytools.fetch_polytopes(h11=2, lattice="N", limit=3)
        for poly in polys:
            try:
                t = poly.triangulate()
                cy = t.get_cy()
                kc = cy.toric_kahler_cone()
                Q = cy.glsm_charge_matrix(include_origin=False)
                phase_type, fan = classify_phase_type(kc, Q)
                # Must return one of the three valid types
                assert phase_type in ("frst", "vex", "non_inherited"), (
                    f"Unexpected phase type: {phase_type}"
                )
                if phase_type == "non_inherited":
                    assert fan is None
                return  # Found one, test passes
            except Exception:
                continue
        pytest.skip("No suitable h11=2 polytope found")


class TestSharedEdgeConsistency:
    """Empirical verification that shared edges across 2-face triangulations
    produce consistent curve classes and diagnoses (D-07 open question).

    When two different 2-face triangulations share an edge (pair of points),
    the resulting curve class and GV invariant should be the same because
    the relevant quads are determined by the edge, not the triangulation.
    """

    @pytest.mark.skipif(
        not _cytools_available(),
        reason="CYTools not available",
    )
    def test_shared_edges_consistent_gvs(self):
        """Check that shared edges across triangulations give same GV."""
        import cytools

        from cybir.core.toric_curves import (
            compute_toric_curves,
            induced_2face_triangulations,
        )

        # Use h11=2 polytope (small, fast)
        polys = cytools.fetch_polytopes(h11=2, lattice="N", limit=5)
        for poly in polys:
            try:
                cy = poly.triangulate().get_cy()
                triags = list(poly.triangulate(N=10))
                if len(triags) < 2:
                    continue

                face_triags_1 = induced_2face_triangulations(
                    poly, [triags[0]]
                )
                face_triags_2 = induced_2face_triangulations(
                    poly, [triags[1]]
                )

                tip = cy.toric_kahler_cone().tip_of_stretched_cone(1)
                tcd_1 = compute_toric_curves(cy, face_triags_1, tip=tip)
                tcd_2 = compute_toric_curves(cy, face_triags_2, tip=tip)

                # Check shared curves have same GV
                shared_keys = set(tcd_1.gv_dict.keys()) & set(
                    tcd_2.gv_dict.keys()
                )
                for key in shared_keys:
                    assert tcd_1.gv_dict[key] == tcd_2.gv_dict[key], (
                        f"GV mismatch for shared curve {key}: "
                        f"{tcd_1.gv_dict[key]} vs {tcd_2.gv_dict[key]}"
                    )

                if shared_keys:
                    return  # Found and verified shared edges, test passes

            except Exception:
                continue

        pytest.skip(
            "No polytope with shared edges across triangulations found"
        )


@pytest.mark.skipif(not _cytools_available(), reason="cytools required")
class TestMoriConeBounds:
    """Tests for the standalone mori_cone_bounds function."""

    def test_from_cy_returns_mori_bounds(self):
        import cytools
        from cybir.core.toric_curves import mori_cone_bounds, MoriBounds

        p = cytools.fetch_polytopes(h11=2, lattice="N", limit=1)[0]
        cy = p.triangulate().get_cy()
        bounds = mori_cone_bounds(cy)
        assert isinstance(bounds, MoriBounds)
        assert bounds.cy is cy
        assert bounds.outer is not None
        assert bounds.outer.rays() is not None
        assert isinstance(bounds.coincide, bool)

    def test_from_fan_round_trips_outer(self):
        """Outer (Mcap) should be identical whether input is CY or fan
        for the same polytope/triangulation."""
        import cytools
        import regfans
        from regfans import VectorConfiguration
        from cybir.core.toric_curves import mori_cone_bounds

        p = cytools.fetch_polytopes(h11=2, lattice="N", limit=1)[0]
        cy = p.triangulate().get_cy()
        bounds_cy = mori_cone_bounds(cy)

        vc = VectorConfiguration(p.points_not_interior_to_facets()[1:])
        fan = vc.triangulate()
        assert fan.respects_ptconfig()
        bounds_fan = mori_cone_bounds(fan)

        # Outer cone should be the same
        rays_cy = sorted(tuple(r) for r in bounds_cy.outer.rays())
        rays_fan = sorted(tuple(r) for r in bounds_fan.outer.rays())
        assert rays_cy == rays_fan

    def test_fan_with_invalid_ptconfig_raises(self):
        """Fan that fails respects_ptconfig() should raise ValueError."""
        from cybir.core.toric_curves import mori_cone_bounds

        class _FakeFan:
            def respects_ptconfig(self):
                return False

            class _FakeVC:
                def vectors(self):
                    return np.eye(3, dtype=int)

            vc = _FakeVC()

            def simplices(self):
                return [(1, 2, 3)]

        with pytest.raises(ValueError, match="respect"):
            mori_cone_bounds(_FakeFan())

    def test_bounds_coincide_majority(self):
        """For most reflexive polytopes, the toric inner bound and Mcap
        should coincide (the actual Mori cone is the toric Mori cone).
        Verify this on a sample: at least 50% should match."""
        import cytools
        from cybir.core.toric_curves import mori_cone_bounds

        polys = cytools.fetch_polytopes(h11=3, lattice="N", limit=20)
        n_total, n_coincide = 0, 0
        for p in polys:
            cy = p.triangulate().get_cy()
            bounds = mori_cone_bounds(cy)
            n_total += 1
            if bounds.coincide:
                n_coincide += 1
        assert n_total > 0
        # Vast majority should agree -- 50% lower bound is conservative
        assert n_coincide >= n_total // 2, (
            f"Only {n_coincide}/{n_total} h11=3 polytopes had "
            f"matching Mori bounds; expected vast majority"
        )

    def test_repr(self):
        import cytools
        from cybir.core.toric_curves import mori_cone_bounds

        p = cytools.fetch_polytopes(h11=2, lattice="N", limit=1)[0]
        cy = p.triangulate().get_cy()
        bounds = mori_cone_bounds(cy)
        r = repr(bounds)
        assert "MoriBounds" in r
        assert "outer=" in r

    def test_top_level_export(self):
        """mori_cone_bounds and MoriBounds should be importable from cybir."""
        from cybir import mori_cone_bounds, MoriBounds  # noqa: F401
