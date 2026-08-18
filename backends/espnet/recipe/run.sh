#!/usr/bin/env bash
# ClearML에서 ESPnet ASR recipe를 실행하는 단일 진입점이다.
# 실행 workspace, dump, exp는 모두 결과 경로 아래에 두어 ESPnet source를 오염시키지 않는다.

set -euo pipefail

data_root=${ML_DATA_ROOT:-/mnt/DB01/clearml/ml-data}
result_root=${ML_RESULT_ROOT:-/mnt/DB01/clearml/ml-results}
task_id=${CLEARML_TASK_ID:-local}

recipe_source=${ESPNET_RECIPE_SOURCE:-/opt/espnet/egs2/TEMPLATE/asr1}
espnet_root=${ESPNET_ROOT:-/opt/espnet}
output_dir=${ESPNET_OUTPUT_DIR:-$result_root/stt/ko/8k/train/$task_id}
workspace=$output_dir/workspace

stage=${ESPNET_STAGE:-3}
stop_stage=${ESPNET_STOP_STAGE:-11}
skip_stages=${ESPNET_SKIP_STAGES:-5 6 7 8 9}

lang=${ESPNET_LANG:-kr_2604espnet_period5-1_noiseaug_8k}
train_set=${ESPNET_TRAIN_SET:-small_period5-1_train}
valid_set=${ESPNET_VALID_SET:-small_period5-1_train_dev}
test_sets=${ESPNET_TEST_SETS:-}

train_data_dir=${ESPNET_TRAIN_DATA_DIR:-$data_root/stt/ko/8k/datasets/period5-1-small/v1/train}
valid_data_dir=${ESPNET_VALID_DATA_DIR:-$data_root/stt/ko/8k/datasets/period5-1-small/v1/valid}
tokenizer_dir=${ESPNET_TOKENIZER_DIR:-$data_root/stt/ko/8k/tokenizers/char/kr-2604-period5-1/v1}
conf_dir=${ESPNET_CONF_DIR:-$data_root/stt/recipes/a198-asr/v1/conf}

asr_config=${ESPNET_ASR_CONFIG:-conf/namz_training/base/train_asr_transformer_period5.yaml}
inference_config=${ESPNET_INFERENCE_CONFIG:-conf/namz_training/decode/decode_asr.yaml}
nlsyms_txt=${ESPNET_NLSYMS_TXT:-$tokenizer_dir/nlsyms.txt}
rir_scp=${ESPNET_RIR_SCP:-$data_root/stt/shared/8k/augmentations/rir/a198/v1/wav.scp}
noise_scp=${ESPNET_NOISE_SCP:-$data_root/stt/shared/8k/augmentations/noise/original2/v1/wav.scp}

ngpu=${ESPNET_NGPU:-1}
num_nodes=${ESPNET_NUM_NODES:-1}
nj=${ESPNET_NJ:-8}
inference_nj=${ESPNET_INFERENCE_NJ:-8}
max_epoch=${ESPNET_MAX_EPOCH:-1}
batch_size=${ESPNET_BATCH_SIZE:-64}
pretrained_model=${ESPNET_PRETRAINED_MODEL:-}
ignore_init_mismatch=${ESPNET_IGNORE_INIT_MISMATCH:-false}

require_file() {
    if [[ ! -f $1 ]]; then
        printf '필수 파일이 없습니다: %s\n' "$1" >&2
        exit 2
    fi
}

require_dir() {
    if [[ ! -d $1 ]]; then
        printf '필수 디렉터리가 없습니다: %s\n' "$1" >&2
        exit 2
    fi
}

link_once() {
    local target=$1
    local link_path=$2

    if [[ -L $link_path ]]; then
        if [[ $(readlink -f "$link_path") != $(readlink -f "$target") ]]; then
            printf '기존 링크가 다른 대상을 가리킵니다: %s\n' "$link_path" >&2
            exit 2
        fi
        return
    fi
    if [[ -e $link_path ]]; then
        printf 'workspace 경로가 이미 존재하며 링크가 아닙니다: %s\n' "$link_path" >&2
        exit 2
    fi
    ln -s "$target" "$link_path"
}

require_dir "$recipe_source"
require_dir "$espnet_root"
require_dir "$train_data_dir"
require_dir "$valid_data_dir"
require_dir "$tokenizer_dir"
require_dir "$conf_dir"
require_file "$tokenizer_dir/tokens.txt"
require_file "$nlsyms_txt"
require_file "$rir_scp"
require_file "$noise_scp"
if [[ -n $pretrained_model ]]; then
    require_file "$pretrained_model"
fi
if [[ $ignore_init_mismatch != true && $ignore_init_mismatch != false ]]; then
    printf 'ESPNET_IGNORE_INIT_MISMATCH는 true 또는 false여야 합니다: %s\n' "$ignore_init_mismatch" >&2
    exit 2
fi

install -d -m 2775 "$workspace/data/$lang"_token_list "$output_dir/dump" "$output_dir/exp"

link_once "$(readlink -f "$recipe_source/asr.sh")" "$workspace/asr.sh"
for name in scripts pyscripts steps utils local cmd.sh db.sh; do
    link_once "$(readlink -f "$recipe_source/$name")" "$workspace/$name"
done
link_once "$conf_dir" "$workspace/conf"
link_once "$train_data_dir" "$workspace/data/$train_set"
link_once "$valid_data_dir" "$workspace/data/$valid_set"
link_once "$tokenizer_dir" "$workspace/data/${lang}_token_list/char"

# 기존 path.sh의 /mnt/WORK01 고정값을 사용하지 않고 현재 ESPnet 설치 위치를 기록한다.
printf '%s\n' \
    "MAIN_ROOT=$espnet_root" \
    'export PATH=$PWD/utils/:$PATH' \
    'export LC_ALL=C' \
    'if [ -f "${MAIN_ROOT}/tools/activate_python.sh" ]; then . "${MAIN_ROOT}/tools/activate_python.sh"; fi' \
    '. "${MAIN_ROOT}/tools/extra_path.sh"' \
    'export OMP_NUM_THREADS=1' \
    'export PYTHONIOENCODING=UTF-8' \
    'export NCCL_SOCKET_IFNAME="^lo,docker,virbr,vmnet,vboxnet"' \
    > "$workspace/path.sh"
chmod 0644 "$workspace/path.sh"

asr_args="--rir_scp $rir_scp --rir_apply_prob 0.2 --noise_scp $noise_scp --noise_apply_prob 0.4 --max_epoch $max_epoch --batch_size $batch_size"
pretrained_args=()
if [[ -n $pretrained_model ]]; then
    pretrained_args+=(
        --pretrained_model "$pretrained_model"
        --ignore_init_mismatch "$ignore_init_mismatch"
    )
fi

cd "$workspace"
./asr.sh \
    --use_streaming false \
    --lang "$lang" \
    --nj "$nj" \
    --inference_nj "$inference_nj" \
    --inference_config "$inference_config" \
    --fs 8k \
    --ngpu "$ngpu" \
    --num_nodes "$num_nodes" \
    --stage "$stage" \
    --stop_stage "$stop_stage" \
    --skip_stages "$skip_stages" \
    "${pretrained_args[@]}" \
    --audio_format wav \
    --feats_type raw \
    --token_type char \
    --nlsyms_txt "$nlsyms_txt" \
    --bpe_nlsyms "$nlsyms_txt" \
    --nbpe 10000 \
    --dumpdir "$output_dir/dump" \
    --expdir "$output_dir/exp" \
    --use_lm false \
    --asr_config "$asr_config" \
    --asr_args "$asr_args" \
    --train_set "$train_set" \
    --valid_set "$valid_set" \
    --test_sets "$test_sets" \
    --speed_perturb_factors "" \
    --asr_speech_fold_length 512 \
    --asr_text_fold_length 150 \
    --min_wav_duration 1 \
    --max_wav_duration 30 \
    "$@"
