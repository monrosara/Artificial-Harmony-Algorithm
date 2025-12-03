import os
import tempfile
import zipfile
import gradio as gr
from pathlib import Path
import shutil

# Import MusicMixer class
from music_mixer_logic import MusicMixer

# Global variables
current_mixer = None
current_samples_dir = None
DEFAULT_SAMPLES_ZIP = "samples.zip"  # Pre-loaded samples archive

def extract_default_samples():
    """Extract pre-loaded samples archive"""
    try:
        if os.path.exists(DEFAULT_SAMPLES_ZIP):
            temp_dir = Path(tempfile.mkdtemp(prefix="default_samples_"))
            with zipfile.ZipFile(DEFAULT_SAMPLES_ZIP, 'r') as zip_ref:
                zip_ref.extractall(temp_dir)
            return str(temp_dir)
        else:
            # If archive doesn't exist, create empty directory
            temp_dir = Path(tempfile.mkdtemp(prefix="empty_samples_"))
            return str(temp_dir)
    except Exception as e:
        print(f"Error extracting archive: {e}")
        temp_dir = Path(tempfile.mkdtemp(prefix="error_samples_"))
        return str(temp_dir)

def process_uploaded_files(files, use_default_samples):
    """Process uploaded files"""
    global current_samples_dir
    
    try:
        if use_default_samples:
            # Use pre-loaded samples
            current_samples_dir = extract_default_samples()
            
            # Check if there are files in the extracted archive
            default_dir = Path(current_samples_dir)
            audio_files = list(default_dir.rglob("*.wav")) + list(default_dir.rglob("*.mp3")) + \
                         list(default_dir.rglob("*.flac")) + list(default_dir.rglob("*.aiff"))
            
            if audio_files:
                return f"✅ Using pre-loaded samples. Found {len(audio_files)} audio files."
            else:
                return "⚠️ No audio files found in pre-loaded archive. Please upload your own files."
        else:
            # User uploads their own files
            if files:
                temp_dir = Path(tempfile.mkdtemp(prefix="user_samples_"))
                file_count = 0
                
                for file in files:
                    file_path = Path(file.name)
                    
                    # If it's a zip archive - extract it
                    if file_path.suffix.lower() == '.zip':
                        with zipfile.ZipFile(file_path, 'r') as zip_ref:
                            zip_ref.extractall(temp_dir)
                            extracted = len(zip_ref.namelist())
                            file_count += extracted
                    else:
                        # Otherwise copy the audio file
                        shutil.copy(file_path, temp_dir / file_path.name)
                        file_count += 1
                
                current_samples_dir = str(temp_dir)
                
                # Check if there are audio files
                audio_files = list(temp_dir.rglob("*.wav")) + list(temp_dir.rglob("*.mp3")) + \
                             list(temp_dir.rglob("*.flac")) + list(temp_dir.rglob("*.aiff"))
                
                if audio_files:
                    return f"✅ Uploaded {file_count} files. Found {len(audio_files)} audio files."
                else:
                    return "⚠️ Files uploaded, but no audio files found (.wav, .mp3, .flac, .aiff)"
            else:
                # Check if current_samples_dir is already set via custom path
                if current_samples_dir and os.path.exists(current_samples_dir):
                    dir_path = Path(current_samples_dir)
                    audio_files = list(dir_path.rglob("*.wav")) + list(dir_path.rglob("*.mp3")) + \
                                 list(dir_path.rglob("*.flac")) + list(dir_path.rglob("*.aiff"))
                    
                    if audio_files:
                        return f"✅ Using custom directory. Found {len(audio_files)} audio files."
                    else:
                        return "⚠️ Custom directory set, but no audio files found."
                else:
                    return "❌ No files uploaded and no custom directory set."
                
    except Exception as e:
        return f"❌ Error processing files: {str(e)}"

def set_custom_path(path, use_default):
    """Set custom samples directory path"""
    global current_samples_dir
    if path and os.path.exists(path):
        current_samples_dir = path
        return f"✅ Custom directory set: {path}"
    else:
        return "❌ Directory not found or path is invalid"

def init_mixer(target_bpm, current_key, use_experimental):
    """Initialize the mixer"""
    global current_mixer, current_samples_dir
    
    if current_samples_dir is None:
        # If nothing selected, use pre-loaded samples
        current_samples_dir = extract_default_samples()
    
    try:
        # Check if directory exists
        if not os.path.exists(current_samples_dir):
            return None, "❌ Sample directory not found"
        
        # Create mixer
        current_mixer = MusicMixer(
            samples_dir=current_samples_dir,
            target_bpm=target_bpm,
            current_key=current_key,
            experimental_mode=use_experimental
        )
        
        # Check if there are samples
        samples = current_mixer.get_all_samples()
        if not samples:
            return None, f"❌ No audio files found. Try uploading different files."
        
        return current_mixer, f"✅ Mixer ready. Analyzed {len(samples)} samples"
        
    except Exception as e:
        return None, f"❌ Initialization error: {str(e)}"

def generate_mix(num_layers, target_bpm, current_key, use_experimental, progress=gr.Progress()):
    """Main mix generation function"""
    global current_mixer
    
    try:
        progress(0.1, desc="🎵 Initializing mixer...")
        
        # Initialize mixer
        mixer, status = init_mixer(target_bpm, current_key, use_experimental)
        if mixer is None:
            return None, status
        
        current_mixer = mixer
        
        progress(0.4, desc="🎵 Analyzing samples and creating composition...")
        
        # Generate mix
        audio_path, description, composition_info = current_mixer.generate_complete_mix(
            num_layers=num_layers
        )
        
        progress(0.8, desc="💾 Saving result...")
        
        if os.path.exists(audio_path):
            # Read file for verification
            file_size = os.path.getsize(audio_path)
            if file_size > 0:
                progress(1.0, desc="✅ Done!")
                return audio_path, description
            else:
                return None, "❌ Error: created empty audio file"
        else:
            return None, "❌ Error: audio file not created"
        
    except Exception as e:
        return None, f"❌ Error creating mix: {str(e)}"

def update_sample_info():
    """Update information about loaded samples"""
    global current_samples_dir
    if current_samples_dir and os.path.exists(current_samples_dir):
        dir_path = Path(current_samples_dir)
        wav_files = list(dir_path.rglob("*.wav"))
        mp3_files = list(dir_path.rglob("*.mp3"))
        flac_files = list(dir_path.rglob("*.flac"))
        aiff_files = list(dir_path.rglob("*.aiff"))
        
        total = len(wav_files) + len(mp3_files) + len(flac_files) + len(aiff_files)
        
        info_text = f"""
        **📊 Sample Statistics:**
        - Total audio files: {total}
        - WAV files: {len(wav_files)}
        - MP3 files: {len(mp3_files)}
        - FLAC files: {len(flac_files)}
        - AIFF files: {len(aiff_files)}
        
        **📂 Source:** {dir_path.name}
        """
        return info_text
    return "Sample information not available"

def cleanup_temp_dirs():
    """Clean up temporary directories"""
    global current_mixer
    if current_mixer:
        current_mixer.cleanup()

# Create Gradio interface
with gr.Blocks(title="Artificial Harmony Algorithm") as demo:
    # Добавляем CSS через мета-тег в HTML
    gr.HTML("""
    <style>
    .warning-text {
        color: #ff6b6b;
        font-weight: bold;
        background-color: #fff3cd;
        padding: 10px;
        border-radius: 5px;
        border: 1px solid #ffc107;
        margin: 10px 0;
    }
    </style>
    """)
    
    gr.Markdown("# 🎵 Artificial Harmony Algorithm")
    gr.Markdown("""
    ### Create unique music mixes from samples!
    
    **Choose sample source:**
    - 🎁 **Use pre-loaded samples** (quick start)
    - 📤 **Upload your own samples** (full control)
    - 🔧 **Advanced: Custom directory path**
    """)
    
    with gr.Row():
        with gr.Column(scale=1):
            # Sample source selection
            gr.Markdown("## 📁 Step 1: Choose Sample Source")
            
            use_default_samples = gr.Checkbox(
                label="🎁 Use pre-loaded samples",
                value=True,
                interactive=True
            )
            
            # Reminder for users - используем HTML с inline стилями
            gr.HTML("""
            <div style="color: #ff6b6b; font-weight: bold; background-color: #fff3cd; padding: 10px; border-radius: 5px; border: 1px solid #ffc107; margin: 10px 0;">
            ⚠️ <b>Important:</b> Uncheck the box above if you're uploading your own samples!
            </div>
            """)
            
            # Optional: Direct path input for advanced users
            with gr.Accordion("🔧 Advanced: Specify custom samples directory (optional)", open=False):
                gr.Markdown("Provide a direct file system path to your samples folder:")
                custom_samples_path = gr.Textbox(
                    label="Custom samples directory path",
                    placeholder="e.g., /path/to/your/samples or C:\\Users\\Name\\samples",
                    interactive=True
                )
                use_custom_path_btn = gr.Button("Use This Directory", variant="secondary", size="sm")
                
                custom_path_status = gr.Textbox(label="Status", interactive=False)
                use_custom_path_btn.click(
                    set_custom_path,
                    inputs=[custom_samples_path, use_default_samples],
                    outputs=[custom_path_status]
                )
            
            with gr.Accordion("📤 Upload your own samples (optional)", open=False):
                file_upload = gr.File(
                    label="Select audio files or ZIP archive",
                    file_types=[".wav", ".mp3", ".flac", ".aiff", ".zip"],
                    file_count="multiple",
                    interactive=True
                )
            
            upload_status = gr.Textbox(
                label="Sample Status",
                value="🎁 Pre-loaded samples ready. Click 'Load Samples'",
                interactive=False
            )
            
            load_samples_btn = gr.Button("📁 Load Samples", variant="primary")
            
            load_samples_btn.click(
                process_uploaded_files,
                inputs=[file_upload, use_default_samples],
                outputs=[upload_status]
            )
            
            gr.Markdown("---")
            
            # Mix settings
            gr.Markdown("## ⚙️ Step 2: Mix Settings")
            
            num_layers = gr.Slider(
                minimum=1, maximum=8, value=3, step=1,
                label="Number of Layers",
                interactive=True
            )
            
            target_bpm = gr.Slider(
                minimum=80, maximum=180, value=128, step=1,
                label="Target BPM (tempo)",
                interactive=True
            )
            
            current_key = gr.Dropdown(
                choices=[f"{i}{j}" for i in range(1, 13) for j in ['A', 'B']],
                value="8A",
                label="Musical Key (Camelot system)",
                interactive=True
            )
            
            use_experimental = gr.Checkbox(
                label="Experimental mode (more unusual combinations)", 
                value=False,
                interactive=True
            )
            
            generate_btn = gr.Button(
                "🎵 Generate Mix",
                variant="primary",
                size="lg"
            )
        
        with gr.Column(scale=2):
            # Results section
            gr.Markdown("## 🎧 Results")
            
            status_info = gr.Markdown(
                "### Ready to work!\n"
                "1. 📁 Choose sample source\n"
                "2. ⚙️ Configure mix settings\n"
                "3. 🎵 Click 'Generate Mix'"
            )
            
            audio_output = gr.Audio(
                label="Generated Mix",
                type="filepath",
                interactive=False
            )
            
            text_output = gr.Markdown(
                "Mix composition info will appear here..."
            )
            
            # Sample information
            with gr.Accordion("📊 Sample Information", open=False):
                sample_info = gr.Markdown("Information will appear after loading samples")
            
            load_samples_btn.click(
                update_sample_info,
                inputs=[],
                outputs=[sample_info]
            )
    
    # Generation handler
    generate_btn.click(
        generate_mix,
        inputs=[num_layers, target_bpm, current_key, use_experimental],
        outputs=[audio_output, text_output]
    )
    
    # Preset examples
    gr.Markdown("---")
    gr.Markdown("### 🚀 Quick Start: Ready Presets")
    
    with gr.Row():
        with gr.Column():
            gr.Markdown("**🎵 Dance Mix**")
            gr.Examples(
                examples=[[3, 128, "8A", False]],
                inputs=[num_layers, target_bpm, current_key, use_experimental],
                label=""
            )
        
        with gr.Column():
            gr.Markdown("**🧪 Experimental**")
            gr.Examples(
                examples=[[4, 140, "5B", True]],
                inputs=[num_layers, target_bpm, current_key, use_experimental],
                label=""
            )
        
        with gr.Column():
            gr.Markdown("**😌 Chill Mix**")
            gr.Examples(
                examples=[[2, 100, "3A", False]],
                inputs=[num_layers, target_bpm, current_key, use_experimental],
                label=""
            )

if __name__ == "__main__":
    # First check for pre-loaded archive
    if os.path.exists(DEFAULT_SAMPLES_ZIP):
        print(f"✅ Found pre-loaded archive: {DEFAULT_SAMPLES_ZIP}")
        print(f"   Size: {os.path.getsize(DEFAULT_SAMPLES_ZIP) / (1024*1024):.1f} MB")
    else:
        print(f"⚠️  Pre-loaded archive not found: {DEFAULT_SAMPLES_ZIP}")
        print("   Users will need to upload their own samples")
    
    # Launch application
    demo.launch(
        server_name="0.0.0.0", 
        server_port=7860, 
        share=False,
        debug=False
    )