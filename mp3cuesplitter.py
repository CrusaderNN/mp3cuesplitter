from cueparser import *
from pydub import AudioSegment
import subprocess, fnmatch, re


def cutOneTrack(input_file, track, output_folder):




    #ffmpeg -ss 30 -t 70 -i inputfile.mp3 -acodec copy outputfile.mp3
    #ffmpeg32 -i in.mp3     -metadata title="The Title You Want" -metadata artist="Artist Name" -metadata album="Name of the Album" out.mp3
    new_filename = removeDisallowedFilenameChars('%02d %s - %s.mp3' % (track.number, track.performer, track.title))

    #last song in cue list has no duration (unable to calculate it from cue file)
    if track.duration:
        #some songs have duaration with 0 microseconds - this will omit .000000 string part automatically - so we should add it
        print track.duration
        print track.duration.microseconds
        if track.duration.microseconds != 0:
            track_duration_string = ('%s' % track.duration)[:-3]
        else:
            track_duration_string = ('%s.000' % track.duration)
        CONVERSTION_COMMAND_TEMPLATE = 'ffmpeg -y -ss %s -t %s -i "%s" -metadata title="%s" -metadata artist="%s" -acodec copy "%s"'
        conversion_command = CONVERSTION_COMMAND_TEMPLATE % (
            ('%s' % offsetToTimedelta(track.offset))[:-3],
            track_duration_string,
            input_file,
            removeDisallowedFilenameChars(track.title),
            removeDisallowedFilenameChars(track.performer),
            os.path.join(output_folder, new_filename))
    else:
        CONVERSTION_COMMAND_TEMPLATE = 'ffmpeg -y -ss %s -i "%s" -metadata title="%s" -metadata artist="%s" -acodec copy "%s"'
        conversion_command = CONVERSTION_COMMAND_TEMPLATE % (
            ('%s' % offsetToTimedelta(track.offset))[:-3],
            input_file,
            removeDisallowedFilenameChars(track.title),
            removeDisallowedFilenameChars(track.performer),
            os.path.join(output_folder, new_filename))


    print conversion_command
    print "subprocess.Popen"
    p = subprocess.Popen(conversion_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    print "p_out, p_err = p.communicate()"
    p_out, p_err = p.communicate()

    if p.returncode != 0:
        raise Exception(
            "Decoding failed. ffmpeg returned error code: {0}\n\nOutput from ffmpeg/avlib:\n\n{1}".format(p.returncode,p_err))
    print "finished"


def cutThemAll(cuefile,output_folder  = None):

    if not os.path.isfile(cuefile):
        print("Cannot open file %s" % cuefile)
        exit(2)

    cuesheet = CueSheet()

    cuesheet.setOutputFormat("%performer% - %title%\n%file%\n%tracks%", "%performer% - %title% - offset:%offset% - duration:%duration%")
    with open(cuefile, "rb") as f:
        cuesheet.setData(f.read().decode('latin-1'))
    cuesheet.parse()

    mp3_path = os.path.dirname(cuefile)
    mp3_filename = cuesheet.file
    mp3_full_filename = os.path.join(mp3_path,mp3_filename)
    print mp3_full_filename
    #print(cuesheet.output())
    #sound = AudioSegment.from_mp3(mp3_full_filename)

    current_time_offset = 0
    for num, track in enumerate(cuesheet.tracks):
        print '-'*80
        print "Processing song %s: %s - %s" %(track.number,track.performer, track.title)
        print track.offset


        print track.duration

        #next_song_offset = current_time_offset + int(track.duration.total_seconds()*1000)
        #print "Cutting song in frame [%s:%s]" %( current_time_offset, next_song_offset)
        #current_time_offset = next_song_offset
        cutOneTrack(mp3_full_filename, track, output_folder)




        #pripev = sound[current_time_offset:next_song_offset]


        #pripev.export("file.mp3", format="mp3")


def findAllCueFiles(input_folder):
    print "findAllCueFiles ",input_folder
    for root, dirs, files in os.walk(input_folder):

        for basename in files:
            if fnmatch.fnmatch(basename, '*.cue'):
                filename = os.path.join(root, basename)
                yield filename


    #cutThemAll(cuefile, 'd:\Music\Mp3SplitOutput')

import unicodedata, string

def removeDisallowedFilenameChars(filename):
    cleanedFilename = unicodedata.normalize('NFKD', unicode(filename)).encode('ASCII', 'ignore')
    return ''.join(c for c in cleanedFilename if c in "-_.() %s%s" % (string.ascii_letters, string.digits))

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument( "-i", "--input_folder", help="folder to look for cue files")
    parser.add_argument( "-o", "--output_folder", help="folder to create  album folders and write split mp3 files")
    parser.add_argument( "-n", help="disable car media friendly mode (abbreviation of folder names)" )
    args = parser.parse_args();

    for cue_file in findAllCueFiles(args.input_folder):
        print '-'*80
        print "Processing cue file '%s'"%cue_file

        cuesheet = CueSheet()
        cuesheet.setOutputFormat('','')
        with open(cue_file, "rb") as f:
            cuesheet.setData(f.read().decode('latin-1'))
        cuesheet.parse()
        cue_path = os.path.dirname(cue_file)
        if not os.path.isfile(os.path.join(cue_path, cuesheet.file)):
            print 'WARNING! No mp3 file found for current cue file, skipping it'
            continue

        this_cue_output_folder = args.output_folder
        matchObj = re.search('A State of Trance (?P<number>\d+)',cue_path)
        if matchObj:
            this_cue_output_folder_chunk = 'ASOT '+ matchObj.group('number')
        else:
            this_cue_output_folder_chunk = unicode (cuesheet.performer +' - ' + cuesheet.title)

        this_cue_output_folder_chunk =    removeDisallowedFilenameChars(this_cue_output_folder_chunk)
        this_cue_output_folder = (os.path.join(args.output_folder,this_cue_output_folder_chunk))
        print "We will output files to '%s' folder" % this_cue_output_folder

        if not os.path.exists(this_cue_output_folder):
            os.makedirs(this_cue_output_folder)
        cutThemAll(cue_file, this_cue_output_folder)
    exit()

    cuefile = args.file
    if not os.path.isfile(cuefile):
        print("Cannot open file %s" % cuefile)
        exit(2)

    cuesheet = CueSheet()
    cuesheet.setOutputFormat(args.header, args.track)
    with open(cuefile, "rb") as f:
        cuesheet.setData(f.read().decode('latin-1'))

    cuesheet.parse()
    try:
        if (args.offset):
            offset = offsetToTimedelta(args.offset)
            print(cuesheet.getTrackByTime(offset))
        elif (args.number):
            num = int(args.number)
            print(cuesheet.getTrackByNumber(num))
        else:
            print(cuesheet.output())
    except ValueError:
        print("Cannot parse int")
        exit()

if __name__ == '__main__':
    main()
