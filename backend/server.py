"""Flask server for serving data to react"""
import datetime
import os
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS, cross_origin
from werkzeug.utils import secure_filename
from moviepy.video.io.VideoFileClip import VideoFileClip
from moviepy.editor import concatenate_videoclips
from stt import transcribe_file
from summarizer import summarize

# Initializing flask app
app = Flask(__name__)
CORS(app, supports_credentials=True)


# Getting current time
x = datetime.datetime.now()
 
@app.route('/api/upload', methods=['POST'])
@cross_origin(supports_credentials=True)
def upload_file():
    print("server received request")
    if request.method == 'POST':
        print("post request")
        video = request.files['video']
        video.save(os.path.join("./uploads", secure_filename(video.filename)))
        return jsonify({'success': True, 'originalVideoPath':
                    'uploads/{video.filename}.mp4'})


clips = []
clipNum = 0
@app.route('/api/clip', methods=['POST'])
def clip():
    data = request.get_json()
    print(data)

    original_video_path = data.get('originalVideoPath')
    start_time = data.get('startTime')
    end_time = data.get('endTime')

    if not original_video_path or start_time is None or end_time is None:
        return jsonify({'error': 'Invalid request data'}), 400

    original_clip = VideoFileClip(original_video_path).subclip(start_time, end_time)
    globals()['clips'].append(original_clip)
    clipped_path = 'clips/clip' + str(globals()['clipNum']) + '.mp4'
    globals()['clipNum'] += 1

    original_clip.write_videofile(clipped_path, codec='libx264')

    return jsonify({'success': True, 'clippedVideoPath': clipped_path})


@app.route('/combineclipsvideo', methods=['GET'])
def combineclipsvideo():
    clips = globals()['clips']

    final_clip_path = 'final_clips_video.mp4'
    final = concatenate_videoclips(clips)
    final.write_videofile(final_clip_path, codec='libx264')

    return send_file(final_clip_path, as_attachment=True)


@app.route('/download', methods=['GET'])
def download():
    data = request.get_json()

    video_path = data.get('videoPath')

    if not video_path:
        return jsonify({'error': 'Invalid request data'}), 400
    
    return send_file(video_path, as_attachment=True)


@app.route('/transcript', methods=['GET'])
def transcript():

    video_path = 'final_clips_video.mp4'

    video = VideoFileClip(video_path)

    audio_path = 'final_clips_audio.wav'
    video.audio.write_audiofile(audio_path)

    response = transcribe_file(audio_path)

    return send_file(video_path, as_attachment=True)

     
# Running app
if __name__ == '__main__':
    app.run(debug=True)