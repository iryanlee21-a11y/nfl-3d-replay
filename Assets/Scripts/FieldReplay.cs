using System.Collections.Generic;
using UnityEngine;

/// <summary>
/// 경기장 좌표 추적 데이터를 재생한다.
/// - ID별 마커를 하나씩 유지하고 프레임 사이를 보간해 이동
/// - 팀 색 (BUF 흰색 / BAL 보라색)
/// - 야드 라인·해시마크·사이드라인을 직접 그림 (1 Unity unit = 1 yard)
/// 조작: Space 재생/정지, ←/→ 한 프레임 이동, R 처음으로, ↑/↓ 재생 속도,
///       C 위에서 보기 ↔ 선수 시점, Tab 시점 선수 변경
/// </summary>
public class FieldReplay : MonoBehaviour
{
    [Header("Data")]
    public string csvPath = "python/data/field_tracks.csv";
    public float sourceFps = 29.97f;

    [Header("Markers")]
    public GameObject playerPrefab;          // 비워두면 캡슐을 자동 생성
    public Color bufColor = Color.white;
    public Color balColor = new Color(0.45f, 0.2f, 0.7f);

    [Header("Field (yards)")]
    public float fieldXMin = -30f, fieldXMax = 12f;
    public float lineOfScrimmageX = 2.1f;
    public bool drawField = true;

    [Header("Cameras")]
    public Camera topCamera;                 // 위에서 보는 카메라
    public CameraRig povRig;                 // 선수 시점 카메라
    public int povPlayerId = 3;              // 기본: 22번 러닝백(144프레임 이후 ID 3)

    const float FieldWidth = 53.33f;
    Dictionary<int, List<FieldTracksLoader.Sample>> data;
    readonly Dictionary<int, Transform> markers = new Dictionary<int, Transform>();
    readonly Dictionary<int, Vector3> velocity = new Dictionary<int, Vector3>();
    int maxFrame;
    float t;                                 // 현재 재생 위치 (프레임 단위, 소수 포함)
    float speed = 0.5f;                      // 기본 0.5배속 (실제 속도는 너무 빨라 보임)
    bool playing = true;

    // 경기장 좌표(X, Y) -> Unity 월드 좌표. 공격 방향(X 감소)이 화면 오른쪽(+x)이 되도록 뒤집는다.
    public static Vector3 ToWorld(Vector2 p) => new Vector3(-p.x, 0f, FieldWidth - p.y);

    void Start()
    {
        data = FieldTracksLoader.Load(csvPath, out maxFrame);
        Debug.Log($"Loaded {data.Count} frames (0~{maxFrame}).");
        if (drawField) DrawField();
        if (topCamera != null)
        {
            Vector3 c = ToWorld(new Vector2((fieldXMin + fieldXMax) / 2f, FieldWidth / 2f));
            topCamera.transform.position = c + Vector3.up * 60f;
            topCamera.transform.rotation = Quaternion.Euler(90f, 0f, 0f);
        }
        SetPov(false);
    }

    void Update()
    {
        if (Input.GetKeyDown(KeyCode.Space)) playing = !playing;
        if (Input.GetKeyDown(KeyCode.RightArrow)) { playing = false; t = Mathf.Min(maxFrame, Mathf.Floor(t) + 1); }
        if (Input.GetKeyDown(KeyCode.LeftArrow)) { playing = false; t = Mathf.Max(0, Mathf.Floor(t) - 1); }
        if (Input.GetKeyDown(KeyCode.R)) t = 0;
        if (Input.GetKeyDown(KeyCode.UpArrow)) speed = Mathf.Min(4f, speed * 2f);
        if (Input.GetKeyDown(KeyCode.DownArrow)) speed = Mathf.Max(0.125f, speed / 2f);
        if (Input.GetKeyDown(KeyCode.C) && povRig != null) SetPov(!povRig.gameObject.activeSelf);
        if (Input.GetKeyDown(KeyCode.Tab)) NextPovPlayer();

        if (playing)
        {
            t += Time.deltaTime * sourceFps * speed;
            if (t > maxFrame) t = 0;          // 반복 재생
        }
        ShowAt(t);
    }

    void ShowAt(float time)
    {
        int f0 = Mathf.FloorToInt(time);
        float a = time - f0;
        var cur = Index(f0);
        var nxt = Index(f0 + 1);
        var seen = new HashSet<int>();

        foreach (var kv in cur)
        {
            var s = kv.Value;
            Vector3 p = ToWorld(s.pos);
            if (nxt.TryGetValue(kv.Key, out var n)) p = Vector3.Lerp(p, ToWorld(n.pos), a);
            Transform m = GetMarker(kv.Key);
            bool wasActive = m.gameObject.activeSelf;
            Vector3 prevV = velocity.ContainsKey(kv.Key) ? velocity[kv.Key] : Vector3.zero;
            velocity[kv.Key] = wasActive ? Vector3.Lerp(prevV, p - m.position, 0.2f) : Vector3.zero;   // 처음 나타난 프레임은 속도 0
            m.position = p;
            m.gameObject.SetActive(true);
            SetColor(m, s.team == "BUF" ? bufColor : balColor);
            seen.Add(kv.Key);
        }
        foreach (var kv in markers)
            if (!seen.Contains(kv.Key)) kv.Value.gameObject.SetActive(false);

        if (povRig != null && markers.TryGetValue(povPlayerId, out var target) && target.gameObject.activeSelf)
        {
            Vector3 v = velocity.TryGetValue(povPlayerId, out var vv) ? vv : Vector3.zero;
            povRig.Follow(target, v);
        }
    }

    void OnGUI()
    {
        var style = new GUIStyle(GUI.skin.label) { fontSize = 20 };
        style.normal.textColor = Color.white;
        string view = (povRig != null && povRig.gameObject.activeSelf) ? $"POV: ID {povPlayerId}" : "Top view";
        GUI.Label(new Rect(12, 8, 700, 30), $"{t / sourceFps:0.0}s / {maxFrame / sourceFps:0.0}s   frame {Mathf.FloorToInt(t)}   x{speed}   {(playing ? "" : "[paused]")}   {view}", style);
    }

    Dictionary<int, FieldTracksLoader.Sample> Index(int frame)
    {
        var d = new Dictionary<int, FieldTracksLoader.Sample>();
        if (data.TryGetValue(frame, out var list)) foreach (var s in list) d[s.id] = s;
        return d;
    }

    Transform GetMarker(int id)
    {
        if (markers.TryGetValue(id, out var m)) return m;
        GameObject go = playerPrefab != null ? Instantiate(playerPrefab) : GameObject.CreatePrimitive(PrimitiveType.Capsule);
        go.name = $"Player_{id}";
        if (playerPrefab == null) go.transform.localScale = new Vector3(0.8f, 1f, 0.8f);   // 높이 약 2야드
        go.transform.SetParent(transform);
        go.SetActive(false);
        markers[id] = go.transform;
        return go.transform;
    }

    static void SetColor(Transform m, Color c)
    {
        foreach (var r in m.GetComponentsInChildren<Renderer>()) r.material.color = c;
    }

    void SetPov(bool on)
    {
        if (povRig != null) povRig.gameObject.SetActive(on);
        if (topCamera != null) topCamera.gameObject.SetActive(!on);
    }

    void NextPovPlayer()
    {
        var ids = new List<int>();
        foreach (var kv in markers) if (kv.Value.gameObject.activeSelf) ids.Add(kv.Key);
        if (ids.Count == 0) return;
        ids.Sort();
        int i = ids.IndexOf(povPlayerId);
        povPlayerId = ids[(i + 1) % ids.Count];
        Debug.Log("POV player: " + povPlayerId);
    }

    void DrawField()
    {
        var root = new GameObject("Field").transform;
        root.SetParent(transform);
        var grass = GameObject.CreatePrimitive(PrimitiveType.Plane);
        grass.transform.SetParent(root);
        Vector3 c = ToWorld(new Vector2((fieldXMin + fieldXMax) / 2f, FieldWidth / 2f));
        grass.transform.position = new Vector3(c.x, -0.01f, c.z);
        grass.transform.localScale = new Vector3((fieldXMax - fieldXMin + 10f) / 10f, 1f, (FieldWidth + 10f) / 10f);
        grass.GetComponent<Renderer>().material.color = new Color(0.2f, 0.45f, 0.15f);

        for (int x = Mathf.CeilToInt(fieldXMin); x <= fieldXMax; x++)
        {
            if (x % 5 == 0) Line(root, new Vector2(x, 0), new Vector2(x, FieldWidth), 0.15f, Color.white);
            foreach (float yh in new[] { 0.6f, 23.58f, 29.75f, FieldWidth - 0.6f })
                Line(root, new Vector2(x, yh - 0.3f), new Vector2(x, yh + 0.3f), 0.08f, Color.white);
        }
        Line(root, new Vector2(fieldXMin, 0), new Vector2(fieldXMax, 0), 0.3f, Color.white);
        Line(root, new Vector2(fieldXMin, FieldWidth), new Vector2(fieldXMax, FieldWidth), 0.3f, Color.white);
        Line(root, new Vector2(lineOfScrimmageX, 0), new Vector2(lineOfScrimmageX, FieldWidth), 0.15f, new Color(0.2f, 0.3f, 0.9f));
    }

    static void Line(Transform parent, Vector2 a, Vector2 b, float width, Color color)
    {
        var go = new GameObject("Line");
        go.transform.SetParent(parent);
        var lr = go.AddComponent<LineRenderer>();
        lr.positionCount = 2;
        lr.SetPosition(0, ToWorld(a) + Vector3.up * 0.02f);
        lr.SetPosition(1, ToWorld(b) + Vector3.up * 0.02f);
        lr.startWidth = lr.endWidth = width;
        lr.material = new Material(Shader.Find("Sprites/Default"));
        lr.startColor = lr.endColor = color;
    }
}
