package main

import (
	"log"
	"os"
	"text/template"
)

var (
	templ  = template.Must(template.ParseFiles("slave.yaml.tmpl"))
	slaves = []string{
		"slave-android",
		"slave-debian-jessie-32",
		"slave-debian-jessie-64",
		"slave-fedora-25-32",
		"slave-fedora-25-64",
		"slave-fedora-26-32",
		"slave-fedora-26-64",
		"slave-mac-cross",
		"slave-mingw",
		"slave-spotify-blob-32",
		"slave-spotify-blob-64",
		"slave-transifex",
		"slave-ubuntu-trusty-32",
		"slave-ubuntu-trusty-64",
		"slave-ubuntu-xenial-32",
		"slave-ubuntu-xenial-64",
		"slave-ubuntu-zesty-32",
		"slave-ubuntu-zesty-64",
		"slave-ubuntu-bionic-32",
		"slave-ubuntu-bionic-64",
		"slave-ubuntu-cosmic-32",
		"slave-ubuntu-cosmic-64",
	}
)

func main() {
	for _, slave := range slaves {
		file, err := os.OpenFile(slave+".yaml", os.O_CREATE|os.O_WRONLY, 0644)
		if err != nil {
			log.Fatalf("Failed to generate slave %s: %v", slave, err)
		}
		defer func() {
			if err := file.Close(); err != nil {
				log.Fatalf("Failed to write slave configuration for %s: %v", slave, err)
			}
		}()

		err = templ.Execute(file, struct {
			Name string
		}{
			slave,
		})
		if err != nil {
			log.Fatalf("Failed to generate slave %s: %v", slave, err)
		}
	}
}
