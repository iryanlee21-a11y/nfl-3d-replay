using System.Collections.Generic;
using UnityEngine;

public class DetectionsPlayer : MonoBehaviour
{
    public string csvPath = "python/data/detections.csv";
    public GameObject playerPrefab;
    public int fieldWidth = 1280;   // 이미지 가로 픽셀
    public int fieldHeight = 720;   // 이미지 세로 픽셀
    public float fieldScale = 10f;  // Unity 월드 스케일
    public float frameDelay = 0.03f; // 프레임당 시간 간격 (약 30fps)

    private Dictionary<int, List<Vector2>> detections;
    private List<GameObject> markers = new List<GameObject>();
    private int currentFrame = 0;
    private bool isPlaying = true;
    private float timer = 0f; // 누적 시간 타이머

    void Start()
    {
        detections = CsvDetectionsLoader.LoadDetections(csvPath);

        if (detections.Count == 0)
        {
            Debug.LogError("No detections loaded from CSV. Check the file path or contents.");
        }
        else
        {
            Debug.Log($"Loaded {detections.Count} frames from CSV.");
        }
    }

    void Update()
    {
        // Space: 재생/일시정지 토글
        if (Input.GetKeyDown(KeyCode.Space)) 
        {
            isPlaying = !isPlaying;
            Debug.Log(isPlaying ? "▶ Playing" : "⏸ Paused");
        }

        // ← / → : 프레임 수동 이동
        if (Input.GetKeyDown(KeyCode.RightArrow)) 
        {
            currentFrame++;
            ShowFrame(currentFrame);
        }
        if (Input.GetKeyDown(KeyCode.LeftArrow)) 
        {
            currentFrame = Mathf.Max(0, currentFrame - 1);
            ShowFrame(currentFrame);
        }

        // 자동 재생 모드일 때만 타이머 누적
        if (!isPlaying) return;

        timer += Time.deltaTime;

        if (timer >= frameDelay)
        {
            timer = 0f;
            ShowFrame(currentFrame);
            Debug.Log("Frame " + currentFrame);
            currentFrame++;
        }
    }

    void ShowFrame(int frame)
    {
        // 이전 프레임의 마커 삭제
        foreach (var m in markers) Destroy(m);
        markers.Clear();

        // 해당 프레임 데이터 없으면 패스
        if (!detections.ContainsKey(frame)) return;

        // 프레임 내 감지된 모든 선수 위치를 마커로 표시
        foreach (var det in detections[frame])
        {
            float x = ((det.x / fieldWidth) - 0.5f) * fieldScale;
            float z = ((1f - det.y / fieldHeight) - 0.5f) * fieldScale; // ← y좌표 반전

            var marker = Instantiate(playerPrefab, new Vector3(x, 0.1f, z), Quaternion.identity);
            markers.Add(marker);
        }
        Debug.Log($"Frame {frame}: {detections[frame].Count} detections");
    }
}