import csv
import random
from datetime import datetime

from qos_routing_gui import (
    generate_random_network,
    compute_total_delay,
    compute_reliability_cost,
    compute_resource_cost,
    compute_total_cost,
    find_best_path_simple,
    q_learning_shortest_path,
    sarsa_shortest_path,
)


def run_single_algorithm(
    alg_name,
    G,
    s,
    d,
    w_delay,
    w_rel,
    w_res,
):
    """
    Verilen algoritma ismine göre uygun yol bulma fonksiyonunu çağırır
    ve yol + metrikleri döner.
    """

    if alg_name == "Basit":
        path = find_best_path_simple(G, s, d, w_delay, w_rel, w_res)
    elif alg_name == "Q-Learning":
        path = q_learning_shortest_path(
            G,
            source=s,
            target=d,
            w_delay=w_delay,
            w_rel=w_rel,
            w_res=w_res,
            episodes=200,
            max_steps=200,
            alpha=0.6,
            gamma=0.9,
            epsilon_start=1.0,
            epsilon_end=0.05,
        )
    elif alg_name == "SARSA":
        path = sarsa_shortest_path(
            G,
            source=s,
            target=d,
            w_delay=w_delay,
            w_rel=w_rel,
            w_res=w_res,
            episodes=200,
            max_steps=200,
            alpha=0.6,
            gamma=0.9,
            epsilon_start=1.0,
            epsilon_end=0.05,
        )
    else:
        raise ValueError(f"Bilinmeyen algoritma: {alg_name}")

    if path is None:
        return None

    total_delay = compute_total_delay(G, path)
    rel_cost = compute_reliability_cost(G, path)
    res_cost = compute_resource_cost(G, path)
    total_cost = compute_total_cost(
        total_delay, rel_cost, res_cost, w_delay, w_rel, w_res
    )

    return {
        "path": path,
        "total_delay": total_delay,
        "rel_cost": rel_cost,
        "res_cost": res_cost,
        "total_cost": total_cost,
    }


def run_experiments(
    n_scenarios: int = 20,
    n_repeats: int = 5,
    n_nodes: int = 250,
    p: float = 0.4,
    w_delay_raw: float = 5.0,
    w_rel_raw: float = 3.0,
    w_res_raw: float = 2.0,
    output_csv: str = "results_experiments.csv",
):
    """
    20 farklı senaryo × 5 tekrar şeklinde deneyler yapar.

    Her senaryoda:
      - Rastgele bir ağ oluşturulur.
      - Rastgele bir kaynak/hedef (S, D) seçilir (S != D).
      - Ağırlıklar GUI'deki varsayılan oranlara göre normalize edilir (5,3,2).
      - Her algoritma (Basit, Q-Learning, SARSA) için yol bulunur ve
        metrikler CSV dosyasına yazılır.
    """

    total_runs = n_scenarios * n_repeats
    print(f"Toplam koşu: {total_runs} (senaryo={n_scenarios}, tekrar={n_repeats})")

    # Normalize weights
    total_w = w_delay_raw + w_rel_raw + w_res_raw
    w_delay = w_delay_raw / total_w
    w_rel = w_rel_raw / total_w
    w_res = w_res_raw / total_w

    algorithms = ["Basit", "Q-Learning", "SARSA"]

    with open(output_csv, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(
            [
                "timestamp",
                "scenario_id",
                "repeat_id",
                "algorithm",
                "n_nodes",
                "n_edges",
                "source",
                "target",
                "w_delay",
                "w_rel",
                "w_res",
                "path_length",
                "total_delay",
                "rel_cost",
                "res_cost",
                "total_cost",
            ]
        )

        run_idx = 0
        for scenario_id in range(1, n_scenarios + 1):
            print(f"\nSenaryo {scenario_id}/{n_scenarios} için ağ oluşturuluyor...")
            G = generate_random_network(n_nodes=n_nodes, p=p)

            nodes = list(G.nodes())
            if len(nodes) < 2:
                print("  Uyarı: Ağda yeterli düğüm yok, bu senaryo atlanıyor.")
                continue

            for repeat_id in range(1, n_repeats + 1):
                run_idx += 1
                print(f"  Tekrar {repeat_id}/{n_repeats} (koşu {run_idx}/{total_runs})")

                # Rastgele ama farklı kaynak/hedef seç
                s, d = random.sample(nodes, 2)

                for alg in algorithms:
                    print(f"    Algoritma: {alg} çalıştırılıyor...", end="", flush=True)
                    result = run_single_algorithm(
                        alg, G, s, d, w_delay, w_rel, w_res
                    )
                    if result is None:
                        print(" yol bulunamadı.")
                        continue

                    print(" tamam.")

                    writer.writerow(
                        [
                            datetime.now().isoformat(timespec="seconds"),
                            scenario_id,
                            repeat_id,
                            alg,
                            len(G.nodes()),
                            len(G.edges()),
                            s,
                            d,
                            w_delay,
                            w_rel,
                            w_res,
                            len(result["path"]),
                            result["total_delay"],
                            result["rel_cost"],
                            result["res_cost"],
                            result["total_cost"],
                        ]
                    )

    print(f"\nDeneyler tamamlandı. Sonuçlar '{output_csv}' dosyasına yazıldı.")


if __name__ == "__main__":
    # Varsayılan deneyleri çalıştır
    run_experiments()


