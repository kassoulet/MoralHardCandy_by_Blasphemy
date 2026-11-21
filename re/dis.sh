# usage: dis.sh START STOP  (obj1.bin = RAM 0x1000.. of the unpacked image)
S=${MHC_SCR:-/tmp/claude-1000/-home-gautier-SynologyDrive-code-current-demoports/32c9b7ad-cb1e-451b-a282-9c45f32c7e6e/scratchpad/mhc}
objdump -D -b binary -mi386 -M intel --adjust-vma=0x1000 --start-address=$1 --stop-address=$2 $S/obj1.bin | sed 's/\t[0-9a-f ]*\t/\t/' | tail -n +8 | cut -c1-80
