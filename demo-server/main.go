package main

import (
	"encoding/json"
	"log"
	"net/http"
	"os"
	"path/filepath"
	"sort"
)

// rawData mirrors the shape of data_{date}.json — only the fields we care about.
type rawData struct {
	Greeting string `json:"greeting"`
	Album    struct {
		Name   string   `json:"name"`
		Artist string   `json:"artist"`
		Year   int      `json:"year"`
		Genres []string `json:"genres"`
	} `json:"album"`
	Weather struct {
		Sunrise struct {
			Temperature int     `json:"temperature"`
			Humidity    float64 `json:"humidity"`
			WindSpeed   string  `json:"windSpeed"`
			Conditions  string  `json:"conditions"`
		} `json:"sunrise"`
	} `json:"weather"`
}

// response is the sanitized shape we serve to the Worker.
type response struct {
	Date     string `json:"date"`
	Greeting string `json:"greeting"`
	Log      string `json:"log"`
	Pipeline string `json:"pipeline"`
	Album    struct {
		Name   string   `json:"name"`
		Artist string   `json:"artist"`
		Year   int      `json:"year"`
		Genres []string `json:"genres"`
	} `json:"album"`
	Weather struct {
		Temperature int     `json:"temperature"`
		Humidity    float64 `json:"humidity"`
		WindSpeed   string  `json:"windSpeed"`
		Conditions  string  `json:"conditions"`
	} `json:"weather"`
}

func findLatestDate(dataDir string) (string, error) {
	entries, err := os.ReadDir(dataDir)
	if err != nil {
		return "", err
	}

	var dates []string
	for _, e := range entries {
		if e.IsDir() {
			dates = append(dates, e.Name())
		}
	}

	sort.Strings(dates)
	return dates[len(dates)-1], nil
}

func latestHandler(dataDir string) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		date, err := findLatestDate(dataDir)
		if err != nil {
			http.Error(w, "could not read data directory", http.StatusInternalServerError)
			return
		}

		dataFile := filepath.Join(dataDir, date, "data_"+date+".json")
		f, err := os.ReadFile(dataFile)
		if err != nil {
			http.Error(w, "could not read data file", http.StatusInternalServerError)
			return
		}

		var raw rawData
		if err := json.Unmarshal(f, &raw); err != nil {
			http.Error(w, "could not parse data file", http.StatusInternalServerError)
			return
		}

		logBytes, _ := os.ReadFile(filepath.Join(dataDir, date, "log_"+date+".txt"))
		pipelineBytes, _ := os.ReadFile(filepath.Join(dataDir, date, "pipeline_"+date+".txt"))

		resp := response{
			Date:     date,
			Greeting: raw.Greeting,
			Log:      string(logBytes),
			Pipeline: string(pipelineBytes),
		}
		resp.Album.Name = raw.Album.Name
		resp.Album.Artist = raw.Album.Artist
		resp.Album.Year = raw.Album.Year
		resp.Album.Genres = raw.Album.Genres
		resp.Weather.Temperature = raw.Weather.Sunrise.Temperature
		resp.Weather.Humidity = raw.Weather.Sunrise.Humidity
		resp.Weather.WindSpeed = raw.Weather.Sunrise.WindSpeed
		resp.Weather.Conditions = raw.Weather.Sunrise.Conditions

		w.Header().Set("Content-Type", "application/json")
		json.NewEncoder(w).Encode(resp)
	}
}

func audioHandler(dataDir string) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		date, err := findLatestDate(dataDir)
		if err != nil {
			http.Error(w, "could not read data directory", http.StatusInternalServerError)
			return
		}
		http.ServeFile(w, r, filepath.Join(dataDir, date, "greeting_"+date+".wav"))
	}
}

func coverHandler(dataDir string) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		date, err := findLatestDate(dataDir)
		if err != nil {
			http.Error(w, "could not read data directory", http.StatusInternalServerError)
			return
		}
		http.ServeFile(w, r, filepath.Join(dataDir, date, "coverart_"+date+".jpg"))
	}
}

func main() {
	dataDir := os.Getenv("DATA_DIR")
	if dataDir == "" {
		dataDir = "/data"
	}

	mux := http.NewServeMux()
	mux.HandleFunc("GET /api/greeting/latest", latestHandler(dataDir))
	mux.HandleFunc("GET /api/greeting/audio", audioHandler(dataDir))
	mux.HandleFunc("GET /api/greeting/cover", coverHandler(dataDir))
	mux.HandleFunc("GET /health", func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusOK)
	})

	log.Println("listening on :8080")
	log.Fatal(http.ListenAndServe(":8080", mux))
}
